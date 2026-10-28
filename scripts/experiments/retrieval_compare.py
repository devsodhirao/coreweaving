"""Frozen retrieval probe and paired agent check; no production defaults change.

Run from the repository root with:
uv run --frozen --with fastembed==0.9.1 python -m scripts.experiments.retrieval_compare --help
"""

import argparse
import asyncio
import hashlib
import itertools
import json
import os
import statistics
import subprocess
import time
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from coreweaving.config import ROOT, source_fingerprint
from coreweaving.corpus import Corpus
from scripts.experiments.retrieval_backend import ExperimentalCorpus, PinnedFastEmbed

DATA = ROOT / "evals/retrieval-probe.json"
RESULTS = ROOT / "results/retrieval-comparison-v1"
BACKEND = Path(__file__).with_name("retrieval_backend.py")
CORPORA = {}
MANIFEST = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    """Never overwrite a measured receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def load_probe():
    data = json.loads(DATA.read_text())
    corpus = Corpus()
    if data["snapshot_id"] != corpus.snapshot_id:
        raise ValueError("Probe snapshot differs")
    for case in data["cases"]:
        for nugget in case["nuggets"]:
            for ref in nugget["acceptable_passages"]:
                if ref["quote"] not in corpus.read(ref["page_id"], ref["section"]).text:
                    raise ValueError(f"Reference quote mismatch: {case['id']}/{nugget['id']}")
    return data


def nugget_metrics(case, hits):
    identities = [(hit["page_id"], hit["section"]) for hit in hits]
    covered, ranks = [], []
    for nugget in case["nuggets"]:
        acceptable = {(r["page_id"], r["section"]) for r in nugget["acceptable_passages"]}
        matching = [i + 1 for i, item in enumerate(identities) if item in acceptable]
        if matching:
            covered.append(nugget["id"])
            ranks.append(min(matching))
    return {
        "covered": covered,
        "nugget_recall": len(covered) / len(case["nuggets"]),
        "all_nuggets": len(covered) == len(case["nuggets"]),
        "first_relevant_rank": min(ranks) if ranks else None,
        "reciprocal_rank": 1 / min(ranks) if ranks else 0,
    }


def ceiling(case, k):
    """Exact best curated coverage attainable with the same page/result caps."""
    identities = sorted(
        {
            (ref["page_id"], ref["section"])
            for nugget in case["nuggets"]
            for ref in nugget["acceptable_passages"]
        }
    )
    best = 0.0
    for count in range(1, min(k, len(identities)) + 1):
        for group in itertools.combinations(identities, count):
            if max(Counter(page for page, _ in group).values()) <= 2:
                hits = [{"page_id": page, "section": section} for page, section in group]
                best = max(best, nugget_metrics(case, hits)["nugget_recall"])
    return best


def selected_cases(data):
    selected, groups = [], set()
    for category in ("plain_language", "exact_api", "workflow"):
        taken = 0
        for case in sorted(data["cases"], key=lambda item: item["id"]):
            if case["category"] == category and case["group_id"] not in groups:
                selected.append(case)
                groups.add(case["group_id"])
                taken += 1
                if taken == 2:
                    break
        if taken != 2:
            raise ValueError("Cannot select two distinct information needs per category")
    return selected


def build(mode, model_dir):
    started = time.monotonic()
    embedder = PinnedFastEmbed(model_dir) if mode == "hybrid" else None
    corpus = ExperimentalCorpus(
        mode=mode, embedder=embedder, cache_dir=ROOT / ".agent-cache/retrieval-index"
    )
    return corpus, time.monotonic() - started


def aggregate(rows, k=6):
    return {
        "queries": len(rows),
        "mean_nugget_recall": statistics.mean(r[f"at_{k}"]["nugget_recall"] for r in rows),
        "all_nuggets_count": sum(r[f"at_{k}"]["all_nuggets"] for r in rows),
        "mean_reciprocal_rank": statistics.mean(r[f"at_{k}"]["reciprocal_rank"] for r in rows),
        "median_query_ms": statistics.median(r["query_seconds"] for r in rows) * 1000,
    }


def offline(args):
    data = load_probe()
    review = json.loads((RESULTS / "instrument-review.json").read_text())
    if review.get("dataset_sha256") != sha(DATA) or review.get("status") != "approved":
        raise ValueError("Independent instrument approval must match the exact dataset")
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": source_fingerprint(),
        "dataset_sha256": sha(DATA),
        "snapshot_id": data["snapshot_id"],
        "backend_sha256": sha(BACKEND),
        "runner_sha256": sha(__file__),
        "protocol_sha256": sha(RESULTS / "protocol.md"),
        "live_case_ids": [case["id"] for case in selected_cases(data)],
    }
    save(RESULTS / "freeze.json", manifest)
    records, arms = [], {}
    for mode in ("baseline", "contextual", "hybrid"):
        corpus, elapsed = build(mode, args.model_dir)
        arms[mode] = {
            "identity": corpus.identity,
            "build_seconds": elapsed,
            "cache_hit": corpus.cache_hit,
        }
        if mode == "hybrid":
            arms[mode].update(windows=len(corpus.window_owners), vector_bytes=corpus.vectors.nbytes)
        for case in data["cases"]:
            started = time.monotonic()
            hits = corpus.search(case["query"], limit=8)["results"]
            records.append(
                {
                    "mode": mode,
                    "case_id": case["id"],
                    "category": case["category"],
                    "group_id": case["group_id"],
                    "query": case["query"],
                    "query_seconds": time.monotonic() - started,
                    "hits": hits,
                    "search_stats": corpus.last_search_stats,
                    "at_6": nugget_metrics(case, hits[:6]),
                    "at_8": nugget_metrics(case, hits),
                }
            )
        save(RESULTS / f"offline-{mode}.json", {"arm": arms[mode], "rows": records[-18:]})
        print(mode, aggregate(records[-18:]), flush=True)
    summaries = {}
    for mode in arms:
        rows = [r for r in records if r["mode"] == mode]
        summaries[mode] = {
            "at_6": aggregate(rows),
            "at_8": aggregate(rows, 8),
            "categories": {
                category: aggregate([r for r in rows if r["category"] == category])
                for category in sorted({r["category"] for r in rows})
            },
            "families": {
                group: aggregate([r for r in rows if r["group_id"] == group])
                for group in sorted({r["group_id"] for r in rows})
            },
        }
    candidate = max(
        ("contextual", "hybrid"),
        key=lambda mode: (
            summaries[mode]["at_6"]["mean_nugget_recall"],
            summaries[mode]["at_6"]["all_nuggets_count"],
            mode == "contextual",
        ),
    )
    baseline, chosen = summaries["baseline"], summaries[candidate]
    gain = chosen["at_6"]["mean_nugget_recall"] - baseline["at_6"]["mean_nugget_recall"]
    threshold = gain >= 0.10 and (
        chosen["categories"]["exact_api"]["all_nuggets_count"]
        >= baseline["categories"]["exact_api"]["all_nuggets_count"]
    )
    save(
        RESULTS / "offline.json",
        {
            "status": "complete",
            "manifest": manifest,
            "arms": arms,
            "summary": summaries,
            "selected_candidate": candidate,
            "primary_recall_gain": gain,
            "meaningful_offline_threshold_met": threshold,
            "ceilings": {c["id"]: {str(k): ceiling(c, k) for k in (6, 8)} for c in data["cases"]},
        },
    )


async def live(args):
    """One Evaluation, fixed paired rows, same runtime/judge, fresh sessions."""
    import weave

    from coreweaving import evaluate
    from coreweaving.agent import Agent, Session
    from coreweaving.budget import model_budget
    from coreweaving.config import init_weave, settings

    global CORPORA, MANIFEST
    data = load_probe()
    offline_result = json.loads((RESULTS / "offline.json").read_text())
    MANIFEST = offline_result["manifest"]
    for expected, actual in (
        (MANIFEST["dataset_sha256"], sha(DATA)),
        (MANIFEST["backend_sha256"], sha(BACKEND)),
        (MANIFEST["source_sha256"], source_fingerprint()),
        (MANIFEST["runner_sha256"], sha(__file__)),
        (MANIFEST["protocol_sha256"], sha(RESULTS / "protocol.md")),
    ):
        if expected != actual:
            raise ValueError("Frozen experiment basis changed")
    config = settings()
    if config.verify_mode != "support":
        raise ValueError("Paired experiment requires unchanged support mode")
    candidate = offline_result["selected_candidate"]
    CORPORA = {mode: build(mode, args.model_dir)[0] for mode in ("baseline", candidate)}
    for mode, corpus in CORPORA.items():
        if corpus.identity != offline_result["arms"][mode]["identity"]:
            raise ValueError("Rebuilt retrieval identity differs from the offline arm")
    rows = []
    for index, case in enumerate(selected_cases(data)):
        refs = {
            (r["page_id"], r["section"])
            for nugget in case["nuggets"]
            for r in nugget["acceptable_passages"]
        }
        for mode in ("baseline", candidate) if index % 2 == 0 else (candidate, "baseline"):
            rows.append(
                {
                    "case_id": case["id"] + "--" + mode,
                    "question_id": case["id"],
                    "retrieval_mode": mode,
                    "prompts": [case["query"]],
                    "expected_behavior": " ".join(a["description"] for a in case["assertions"]),
                    "assertions": case["assertions"],
                    "minimum_pages": 0,
                    "require_code": False,
                    "reference_evidence": [
                        CORPORA[mode].read(p, s).evidence(f"R{i}")
                        for i, (p, s) in enumerate(sorted(refs), 1)
                    ],
                }
            )
    directory = RESULTS / "live"
    directory.mkdir(exist_ok=False)
    evaluate.RUN_DIRECTORY = directory
    save(directory / "dataset.json", rows)
    save(
        directory / "manifest.json",
        {
            **MANIFEST,
            "candidate": candidate,
            "budget_usd": 5,
            "agent_model": config.agent_model,
            "judge_model": config.judge_model,
            "cache_enabled": config.cache_enabled,
            "provider_effort": "unspecified, unchanged",
            "planned_order": [r["case_id"] for r in rows],
        },
    )
    os.environ["WEAVE_PARALLELISM"] = "1"
    halted = []

    class StoppingJudge(evaluate.QualityJudge):
        @weave.op()
        async def score(
            self,
            output: dict,
            prompts: list[str],
            expected_behavior: str,
            reference_evidence: list[dict],
            minimum_pages: int,
            require_code: bool,
            assertions: list[dict] | None = None,
        ) -> dict:
            if halted:
                raise RuntimeError("Comparison stopped after an operational failure")
            try:
                result = await super().score(
                    output,
                    prompts,
                    expected_behavior,
                    reference_evidence,
                    minimum_pages,
                    require_code,
                    assertions,
                )
                if result.get("judge_error"):
                    halted.append(result["judge_error"])
                return result
            except Exception as exc:
                if not halted:
                    halted.append(type(exc).__name__)
                raise

    class RetrievalModel(weave.Model):
        source_sha256: str
        retrieval_backend_sha256: str

        @weave.op()
        async def predict(
            self, prompts: list[str], case_id: str, question_id: str, retrieval_mode: str
        ) -> dict:
            if halted:
                raise RuntimeError("Comparison stopped after an operational failure")
            try:
                identity = {
                    "case_id": case_id,
                    "question_id": question_id,
                    "prediction_id": str(uuid.uuid4()),
                    "retrieval_mode": retrieval_mode,
                    "verify_mode": "support",
                    **evaluate.evaluation_call_ids(),
                }
                attrs = {f"coreweaving.experiment.{k}": v for k, v in identity.items() if v}
                attrs.update(
                    {
                        "coreweaving.retrieval_backend_sha256": self.retrieval_backend_sha256,
                        "coreweaving.retrieval_dataset_sha256": MANIFEST["dataset_sha256"],
                        "weave.eval.example_id": case_id,
                    }
                )
                if identity.get("evaluation_call_id"):
                    attrs["weave.eval.run_id"] = identity["evaluation_call_id"]
                if identity.get("predict_and_score_call_id"):
                    attrs["weave.eval.predict_and_score_call_id"] = identity[
                        "predict_and_score_call_id"
                    ]
                if (
                    source_fingerprint() != self.source_sha256
                    or sha(BACKEND) != self.retrieval_backend_sha256
                ):
                    raise ValueError("Runtime or retrieval backend changed during live comparison")
                print("START", case_id, flush=True)
                turn = await asyncio.to_thread(
                    Agent(CORPORA[retrieval_mode], config).run,
                    prompts[0],
                    Session(),
                    eval_attributes=attrs,
                )
                result = {**turn, **identity, "turns": [turn], "agent_metrics": turn["metrics"]}
                evaluate.persist_record(directory, "predictions", result, result)
                if (
                    source_fingerprint() != self.source_sha256
                    or sha(BACKEND) != self.retrieval_backend_sha256
                ):
                    raise ValueError("Runtime or retrieval backend changed during the turn")
                if turn.get("kind") == "error" or turn.get("error_type"):
                    halted.append(turn.get("error_type") or "AgentOperationalError")
                    raise RuntimeError("Saved failed turn; no further paid cells will run")
                return result
            except Exception as exc:
                if not halted:
                    halted.append(type(exc).__name__)
                raise

    client = init_weave()
    evaluation = weave.Evaluation(
        name="coreweaving-retrieval-comparison",
        evaluation_name="retrieval-comparison-v1",
        dataset=weave.Dataset(name="coreweaving-retrieval-probe-v1", rows=rows),
        trials=1,
        scorers=[
            StoppingJudge(
                name="documentation-quality",
                judge_model=config.judge_model,
                cache_enabled=config.cache_enabled,
            )
        ],
        metadata={**MANIFEST, "candidate": candidate},
    )
    error, call, summary = None, None, None
    with model_budget(5) as budget:
        try:
            summary, call = await evaluation.evaluate.call(
                evaluation,
                RetrievalModel(
                    name="coreweaving-retrieval-probe",
                    source_sha256=MANIFEST["source_sha256"],
                    retrieval_backend_sha256=MANIFEST["backend_sha256"],
                ),
            )
        except Exception as exc:
            error = type(exc).__name__
        finally:
            cases = [
                json.loads(p.read_text()) for p in sorted((directory / "cases").glob("*.json"))
            ]
            complete = len(cases) == 12 and not any(c["scores"].get("judge_error") for c in cases)
            save(
                directory / "summary.json",
                {
                    "status": "complete" if complete and not error else "incomplete",
                    "error": error,
                    "halted": halted,
                    "expected_cases": 12,
                    "scored_cases": len(cases),
                    "budget": budget.snapshot(),
                    "evaluation_call_id": call.id if call else None,
                    "evaluation_url": call.ui_url if call else None,
                    "weave_summary": summary,
                    "remote_delivery": "not yet checked; local completion does not establish delivery",
                },
            )
    client.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("offline", "live"))
    parser.add_argument("--model-dir", type=Path, default=ROOT / ".agent-cache/bge-small-pinned")
    args = parser.parse_args()
    if args.stage == "offline":
        offline(args)
    else:
        asyncio.run(live(args))


if __name__ == "__main__":
    main()
