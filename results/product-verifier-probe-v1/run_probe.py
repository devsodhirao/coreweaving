"""Bounded stored-draft verifier comparison; never edits or runs Agent.run."""

import argparse
import copy
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

from coreweaving.agent import (
    Agent,
    Candidate,
    Session,
    TaskOutcome,
    citation_contract,
    parse_live_verdict,
    python_syntax_issues,
)
from coreweaving.budget import model_budget
from coreweaving.config import ROOT, Settings, source_fingerprint
from coreweaving.corpus import Corpus
from coreweaving.llm import LanguageModel
from coreweaving.metrics import summarize

OUT = ROOT / "results/product-verifier-probe-v1"
SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"
EXPECTED_SOURCE = "68af74ec20b4db584cc21b2b3a102afef77c847130cf9eed9490edd2077709dc"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def stored_case(path, attempt, name):
    data = json.loads(path.read_text())
    candidate = data["verification_attempts"][attempt - 1]["candidate"]
    stop = next(
        i
        for i, action in enumerate(data["actions"])
        if action["tool"] == "submit_answer" and action["input"]["answer"] == candidate["answer"]
    )
    actions = copy.deepcopy(data["actions"][:stop])
    evidence = {}
    for action in actions:
        result = action["result"]
        if action["tool"] == "read_page" and "source_id" in result:
            evidence[result["source_id"]] = copy.deepcopy(result)
    return {
        "id": name,
        "control_kind": "stored_adjudication_candidate_not_assumed_gold",
        "source_file": str(path.relative_to(ROOT)),
        "source_file_sha256": digest(path),
        "source_attempt": attempt,
        "candidate": candidate,
        "question": data["question"],
        "history": data["conversation_context"],
        "evidence": evidence,
        "actions": actions,
        "task_plan": data["task_plan"],
    }


def prepare():
    assert source_fingerprint() == EXPECTED_SOURCE
    overview = stored_case(
        ROOT / "results/product-repair-v1/preset-smoke/result.json",
        3,
        "overview-synthesis",
    )
    contrast = stored_case(
        next((ROOT / "results/product-repair-regression-v1/predictions").glob("02-*.json")),
        3,
        "ops-versus-agents",
    )
    overview["expected_assessment"] = (
        "Adjudication candidate: likely acceptable as a scoped role comparison and explicitly "
        "labelled suggested workflow. S1 supports production turn scoring, S2 supports dataset "
        "evaluation, and S7 supports exploring agent activity. Prior auditor both called the "
        "production claim supported and marked it partial. This expectation is not a gold label; "
        "specific residual unsupported claims or a task gap can justify rejection."
    )
    contrast["expected_assessment"] = (
        "Adjudication candidate: likely acceptable as a qualified synthesis that a bare Op is not "
        "the documented route to agent conversations/turns, with explicit alternative APIs and "
        "integration caveats. The Ops body was not read, so rejection of the definitive opening "
        "remains a possible defensible finding. Do not assume acceptance."
    )
    invented = copy.deepcopy(contrast)
    invented.update(id="invented-argument", control_kind="synthetic_unsupported_negative")
    invented["candidate"]["answer"] += (
        "\n\nSet `capture_ops_as_turns=True` on `weave.start_conversation(...)`. This documented "
        "argument automatically converts every plain `@weave.op` call into an agent turn, "
        "without calling `start_turn`. [S5]"
    )
    invented["expected_assessment"] = (
        "Reject: capture_ops_as_turns is an invented argument and automatic Op-to-turn conversion "
        "is unsupported by S5. The valid citation structure must not authorize this product claim."
    )
    incompatible = copy.deepcopy(overview)
    incompatible.update(
        id="automatic-evaluation-to-signals", control_kind="synthetic_unsupported_negative"
    )
    incompatible["candidate"]["answer"] += (
        "\n\nAfter `evaluation.evaluate(model)` finishes, Weave automatically creates and enables "
        "production Signals from every scorer in that Evaluation. No separate Signal setup is "
        "needed: all subsequent agent turns are scored by those same evaluation scorers. [S1][S2]"
    )
    incompatible["expected_assessment"] = (
        "Reject: dataset Evaluation does not establish automatic creation/enabling of production "
        "Signals or scoring all future turns. The supplied separate feature descriptions do not "
        "support this asserted integration."
    )
    cases = [overview, contrast, invented, incompatible]
    for case in cases:
        candidate = Candidate.model_validate(case["candidate"])
        assert not citation_contract(
            candidate.answer, candidate.kind, candidate.source_ids, case["evidence"]
        )
        assert not python_syntax_issues(candidate.answer)
        assert all(key in case["evidence"] for key in candidate.source_ids)
    write(OUT / "candidates.json", cases)
    schedule = []
    for i, case in enumerate(cases):
        for model in [SONNET, OPUS] if i % 2 == 0 else [OPUS, SONNET]:
            schedule.append({"case_id": case["id"], "model": model})
    protocol = {
        "schema_version": 1,
        "status": "frozen_before_calls",
        "created_at": datetime.now(UTC).isoformat(),
        "source_sha256": EXPECTED_SOURCE,
        "recorded_candidate_runtime_source_sha256": "55c77715c7224fd844a499e93b1a816abfa686db2b848b19991c0a56b28fe794",
        "runtime_difference": "Only telemetry.py dataset-reference preservation changed after these candidates. Agent.verify, llm.py and config.py are unchanged. This probe does not initialize Weave export.",
        "verifier_file_sha256": {
            name: digest(ROOT / "src/coreweaving" / name)
            for name in ("agent.py", "llm.py", "config.py")
        },
        "script_sha256": digest(Path(__file__)),
        "candidates_sha256": digest(OUT / "candidates.json"),
        "purpose": "Paired diagnostic of unchanged source-verification behavior on two stored adjudication candidates and two clearly labelled synthetic negative controls.",
        "models": [SONNET, OPUS],
        "effort": "medium",
        "verify_mode": "support",
        "max_provider_calls": 8,
        "returned_usage_budget_usd": 2,
        "budget_note": "Existing conservative model_budget reservations; SDK retries disabled; stops on unpriced/failed calls. Not a billing cap.",
        "schedule": schedule,
        "reconstruction": "Exact stored candidate; current-question history; original read_page result objects and action prefix strictly before the selected submission. No future reads, source ID minting, task changes or draft repair.",
        "method": "Ordinary Agent.verify, recovery=False/full_recheck=False. Only Settings.agent_model differs. Current prompts, schemas, deterministic guards, 4000 output cap and cache settings retained. No Agent.run/planner/tool execution or weave.init/export initialization.",
        "assessment": "Acceptance requires the final app verdict, not raw provider passed. Delivery/parse failures and guard failures remain distinct from semantic rejection. Any primary-auditor recommendation must weigh both adjudication candidates and both unsupported negatives; four fixtures are not a quality benchmark.",
        "limitations": "No generated-code execution; source examples and payloads are public snapshot data. Paired calls can have different cache warmth. One sample per model/candidate cannot estimate reliability or causally predict end-to-end latency.",
    }
    write(OUT / "protocol.json", protocol)
    print(
        json.dumps(
            {
                "prepared": True,
                "protocol_sha256": digest(OUT / "protocol.json"),
                "candidates_sha256": protocol["candidates_sha256"],
            }
        )
    )


class CapturedClient:
    def __init__(self, client, records, counter):
        self.inner, self.records, self.counter = client, records, counter
        self.messages = SimpleNamespace(create=self.create)

    def with_options(self, **kwargs):
        self.records["client_options"] = kwargs
        return CapturedClient(self.inner.with_options(**kwargs), self.records, self.counter)

    def create(self, **kwargs):
        if self.counter[0] >= 8:
            raise RuntimeError("Frozen eight-call limit reached")
        self.counter[0] += 1
        self.records["provider_request"] = copy.deepcopy(kwargs)
        response = self.inner.messages.create(**kwargs)
        self.records["provider_response"] = response.model_dump(exclude_none=True)
        return response


class CapturedModel:
    def __init__(self, counter):
        self.records = {}
        self.inner = LanguageModel()
        self.inner.client = CapturedClient(self.inner.client, self.records, counter)

    def call(self, **kwargs):
        self.records["verifier_call"] = copy.deepcopy(
            {k: v for k, v in kwargs.items() if k != "span_parent"}
        )
        return self.inner.call(**kwargs)


def run():
    protocol = json.loads((OUT / "protocol.json").read_text())
    assert protocol["script_sha256"] == digest(Path(__file__))
    assert protocol["candidates_sha256"] == digest(OUT / "candidates.json")
    assert not (OUT / "summary.json").exists(), "No reruns allowed in this frozen probe"
    load_dotenv(ROOT / ".env")
    corpus = Corpus()
    cases = {case["id"]: case for case in json.loads((OUT / "candidates.json").read_text())}
    counter, results = [0], []
    stopped = None
    with model_budget(2) as budget:
        for index, spec in enumerate(protocol["schedule"], 1):
            assert source_fingerprint() == EXPECTED_SOURCE, "Runtime changed after fixture freeze"
            case = cases[spec["case_id"]]
            model = CapturedModel(counter)
            agent = Agent(
                corpus, Settings(project="local/verifier-probe", agent_model=spec["model"]), model
            )
            session = Session(
                history=copy.deepcopy(case["history"]), evidence=copy.deepcopy(case["evidence"])
            )
            candidate = Candidate.model_validate(case["candidate"])
            task_plan = tuple(TaskOutcome.model_validate(item) for item in case["task_plan"])
            began = time.monotonic()
            receipt = {
                **spec,
                "index": index,
                "control_kind": case["control_kind"],
                "protocol_sha256": digest(OUT / "protocol.json"),
                "source_sha256": EXPECTED_SOURCE,
            }
            try:
                verdict = agent.verify(
                    candidate,
                    session,
                    case["question"],
                    copy.deepcopy(case["actions"]),
                    task_plan=task_plan,
                )
                receipt["verdict"] = verdict.model_dump()
                raw = model.records.get("provider_response", {})
                blocks = [
                    b
                    for b in raw.get("content", [])
                    if b.get("type") == "tool_use" and b.get("name") == "record_verdict"
                ]
                if len(blocks) != 1 or raw.get("stop_reason") == "max_tokens":
                    receipt["classification"] = "verdict_delivery_failure"
                else:
                    try:
                        parsed = parse_live_verdict(blocks[0]["input"])
                        receipt["raw_parsed_verdict"] = parsed.model_dump()
                        semantic_positive = (
                            parsed.passed
                            and all(
                                c.status == "supported" and c.scope_status == "supported"
                                for c in parsed.claims
                                if c.kind == "product"
                            )
                            and all(o.status == "answered" for o in parsed.outcome_assessments)
                        )
                        receipt["classification"] = (
                            "accepted"
                            if verdict.passed
                            else "record_or_release_guard_failure"
                            if semantic_positive
                            else "semantic_rejection"
                        )
                    except (ValueError, TypeError, KeyError) as exc:
                        receipt["classification"] = "verdict_parse_failure"
                        receipt["parse_error_type"] = type(exc).__name__
            except Exception as exc:
                receipt["classification"] = "request_or_runtime_failure"
                receipt["error_type"] = type(exc).__name__
                stopped = type(exc).__name__
            receipt.update(
                elapsed_seconds=round(time.monotonic() - began, 4),
                metrics=summarize(agent.llm.calls, []),
                records=model.records,
                budget=budget.snapshot(),
            )
            output = OUT / f"{index:02d}-{spec['case_id']}-{spec['model']}.json"
            write(output, receipt)
            results.append(
                {
                    "index": index,
                    **spec,
                    "classification": receipt["classification"],
                    "elapsed_seconds": receipt["elapsed_seconds"],
                    "estimated_usd": receipt["metrics"]["estimated_usd"],
                    "receipt": str(output.relative_to(ROOT)),
                    "receipt_sha256": digest(output),
                }
            )
            write(
                OUT / "summary.json",
                {
                    "status": "stopped"
                    if stopped
                    else "complete"
                    if index == len(protocol["schedule"])
                    else "in_progress",
                    "protocol_sha256": digest(OUT / "protocol.json"),
                    "source_sha256": EXPECTED_SOURCE,
                    "provider_calls": counter[0],
                    "stopped_reason": stopped,
                    "budget": budget.snapshot(),
                    "results": results,
                },
            )
            print(json.dumps(results[-1]), flush=True)
            if stopped:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else run()
