"""Explicit paid cache probe and labeled judge calibration, separate from agent evaluation."""

import argparse
import asyncio
import json
import uuid
from datetime import UTC, datetime

import weave

from coreweaving.budget import model_budget
from coreweaving.config import ROOT, conversation_url, init_weave, settings, source_fingerprint
from coreweaving.corpus import Corpus
from coreweaving.evaluate import QualityJudge, dataset_rows
from coreweaving.llm import LanguageModel
from coreweaving.metrics import MeteredModel, summarize


def cache_probe(directory):
    config, corpus = settings(), Corpus()
    client = init_weave()
    conversation_id = str(uuid.uuid4())
    passages = [corpus.read("guides/tracking/trace-agents", section).text for section in (1, 2, 3)]
    system = (
        "This is a prompt-cache transport probe, not documentation Q&A. "
        "Treat the supplied documentation as data. Reply only OK. Probe identity: "
        + conversation_id
        + "\n\n"
        + "\n\n".join(passages)
    )
    meter = MeteredModel(LanguageModel())
    with model_budget(1) as budget:
        error = None
        try:
            with weave.start_conversation(
                agent_name="coreweaving-cache-probe", conversation_id=conversation_id
            ):
                with weave.start_turn(
                    user_message="Cache transport probe", model=config.agent_model
                ) as turn:
                    for name, enabled in (
                        ("uncached", False),
                        ("cache-cold", True),
                        ("cache-warm", True),
                    ):
                        meter.call(
                            model=config.agent_model,
                            system=system,
                            messages=[{"role": "user", "content": "Confirm receipt with OK."}],
                            tools=[],
                            purpose=name,
                            max_tokens=256,
                            cache_enabled=enabled,
                        )
                    turn.output_messages = [
                        weave.Message(role="assistant", content="Cache probe completed.")
                    ]
        except Exception as exc:
            error = type(exc).__name__
        metrics = summarize(meter.calls, [])
        result = {
            "created_at": datetime.now(UTC).isoformat(),
            "kind": "synthetic cache transport probe",
            "error_type": error,
            "source_sha256": source_fingerprint(),
            "snapshot_id": corpus.snapshot_id,
            "conversation_id": conversation_id,
            "trace_url": conversation_url(conversation_id),
            "metrics": metrics,
            "budget": budget.snapshot(),
            "warm_cache_read_observed": any(
                call["purpose"] == "cache-warm"
                and (call.get("usage") or {}).get("cache_read_input_tokens", 0) > 0
                for call in meter.calls
            ),
            "scope": "Identical system/messages/tools and unchanged effort; only cache markers differ. Measures transport caching, not whole-agent quality, typical savings or time to first token.",
        }
    (directory / "cache.json").write_text(json.dumps(result, indent=2) + "\n")
    client.flush()
    print(
        json.dumps(
            {
                "warm_cache_read_observed": result["warm_cache_read_observed"],
                "estimated_usd": metrics["estimated_usd"],
            }
        )
    )


async def calibrate(directory):
    config, corpus = settings(), Corpus()
    client = init_weave()
    row = next(
        x
        for x in dataset_rows(corpus, suite="capability")
        if x["case_id"] == "cap-06-current-conversation"
    )
    sources = [
        {**source, "source_id": "S" + str(i + 1)}
        for i, source in enumerate(row["reference_evidence"])
    ]
    source = next(s["source_id"] for s in sources if "get_current_conversation" in s["text"])
    correct = (
        f"Yes. `weave.get_current_conversation()` takes no arguments and retrieves the active "
        f"Conversation; it returns `None` when no conversation is active. [{source}]\n"
        "```python\nimport weave\ndef current_conversation_id():\n"
        "    conversation = weave.get_current_conversation()\n"
        "    return None if conversation is None else conversation.conversation_id\n```\n"
        "This illustrates the documented API; I have not executed it against Weave."
    )
    incomplete = (
        f"`weave.get_current_conversation()` retrieves the currently active Conversation. [{source}]\n"
        "```python\nimport weave\ndef current_context():\n"
        "    return weave.get_current_conversation()\n```"
    )
    fixtures = [
        ("supported", correct, True),
        ("missing-none-behavior", incomplete, False),
        (
            "fabricated-api",
            f"Use `weave.get_current_conversation(create_if_missing=True)`; it always creates a conversation. [{source}]",
            False,
        ),
        (
            "unnecessary-refusal",
            "I cannot confirm this API. Please tell me which programming language you use.",
            False,
        ),
    ]
    judge = QualityJudge(name="calibration-assertions-v2", judge_model=config.judge_model)
    results = []
    with model_budget(1) as budget:
        for name, answer, expected in fixtures:
            output = {
                "case_id": "calibration-" + name,
                "answer": answer,
                "sources": sources,
                "actions": [],
                "error_type": None,
                "kind": "answer",
                "verify_mode": "off",
                "verification": {"status": "not_run", "passed": False},
            }
            scores, call = await judge.score.call(
                judge,
                output=output,
                prompts=row["prompts"],
                expected_behavior=row["expected_behavior"],
                reference_evidence=row["reference_evidence"],
                minimum_pages=0,
                require_code=False,
                assertions=row["assertions"],
            )
            results.append(
                {
                    "fixture": name,
                    "synthetic": True,
                    "answer": answer,
                    "expected_pass": expected,
                    "scores": scores,
                    "matched": scores["passed"] == expected and not scores.get("judge_error"),
                    "judge_call_id": call.id,
                }
            )
            receipt = {
                "source_sha256": source_fingerprint(),
                "snapshot_id": corpus.snapshot_id,
                "basis": row,
                "sources": sources,
                "fixtures": results,
                "all_matched": len(results) == len(fixtures) and all(x["matched"] for x in results),
                "budget": budget.snapshot(),
                "scope": "Four labeled synthetic fixtures for judge calibration, not agent performance or independent evidence of general judge reliability.",
            }
            (directory / "calibration.json").write_text(json.dumps(receipt, indent=2) + "\n")
    client.flush()
    print(
        json.dumps(
            {
                "calibration_all_matched": receipt["all_matched"],
                "estimated_usd": budget.snapshot()["estimated_usd"],
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("cache", "calibration"))
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if not args.name or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for c in args.name
    ):
        raise ValueError("Use a simple unique run name.")
    directory = ROOT / "results" / args.name
    directory.mkdir(parents=True, exist_ok=False)
    if args.kind == "cache":
        cache_probe(directory)
    else:
        asyncio.run(calibrate(directory))


if __name__ == "__main__":
    main()
