"""One disclosed operational resumption, preserving the interrupted comparison."""

import asyncio
import importlib.util
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from coreweaving import evaluate
from coreweaving.agent import Agent, Session
from coreweaving.budget import model_budget
from coreweaving.config import ROOT, init_weave, settings, source_fingerprint
from coreweaving.corpus import Corpus
from scripts.experiments.retrieval_backend import PinnedFastEmbed

spec = importlib.util.spec_from_file_location("original_retrieval_run", Path(__file__).with_name("run.py"))
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
HERE, CASES, BACKEND, REUSE = original.HERE, original.CASES, original.BACKEND, original.REUSE
save, sha = original.save, original.sha


async def main():
    frozen = json.loads((HERE / "freeze.json").read_text())
    previous = json.loads((HERE / "summary.json").read_text())
    assert previous["status"] == "incomplete" and previous["scored"] == 4
    assert previous["budget"]["unpriced_calls"] == 0
    assert sha(HERE / "run.py") == frozen["runner_sha256"]
    assert sha(CASES) == frozen["cases_sha256"] and sha(BACKEND) == frozen["backend_sha256"]
    assert sha(REUSE) == frozen["reuse_helper_sha256"]
    assert source_fingerprint() == frozen["source_sha256"]
    cfg = settings()
    assert asdict(cfg) == frozen["settings"]
    remaining = frozen["estimated_budget_usd"] - previous["budget"]["known_estimated_usd"]
    save(HERE / "resumption-freeze.json", {"created_at": datetime.now(UTC).isoformat(), "script_sha256": sha(Path(__file__)), "policy_sha256": sha(HERE / "resumption.md"), "original_freeze_sha256": sha(HERE / "freeze.json"), "prior_summary_sha256": sha(HERE / "summary.json"), "remaining_allowance_usd": remaining})
    spec = importlib.util.spec_from_file_location("reuse_hybrid", REUSE)
    reuse = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reuse)
    start = time.monotonic()
    corpora = {"baseline": Corpus(), "hybrid": reuse.CachedHybrid(mode="hybrid", embedder=PinnedFastEmbed(ROOT / ".agent-cache/bge-small-pinned"), cache_dir=ROOT / ".agent-cache/retrieval-index")}
    assert corpora["hybrid"].identity == frozen["hybrid_identity"]
    assert corpora["hybrid"].cache_receipt == frozen["vector_cache"]
    preparation_seconds = time.monotonic() - start
    data = json.loads(CASES.read_text())
    evaluate.RUN_DIRECTORY = HERE / "resumption"
    client = init_weave()
    judge = evaluate.QualityJudge(name="retrieval-live-v3-quality", judge_model=cfg.judge_model)
    rows, error, retries = list(previous["rows"]), None, []
    with model_budget(remaining) as budget:
        for index, cell in enumerate(frozen["planned_order"][4:], 5):
            key = f"{index:02d}-{cell['case_id']}--t{cell['trial']}--{cell['arm']}"
            folder = HERE / "attempts" / key
            print("START", key, flush=True)
            try:
                assert source_fingerprint() == frozen["source_sha256"]
                case = next(c for c in data["cases"] if c["id"] == cell["case_id"])
                if index == 5:
                    turn = json.loads((folder / "result.json").read_text())
                else:
                    folder.mkdir(parents=True, exist_ok=False)
                    save(folder / "submission.json", {**cell, "submitted_at": datetime.now(UTC).isoformat(), "query": case["query"]})
                    turn = await asyncio.to_thread(Agent(corpora[cell["arm"]], cfg).run, case["query"], Session(), eval_attributes={"coreweaving.experiment": "retrieval-live-v3", "coreweaving.retrieval_mode": cell["arm"], "coreweaving.case_id": case["id"], "coreweaving.trial": cell["trial"]})
                    save(folder / "result.json", turn)
                assert turn["source_sha256"] == frozen["source_sha256"]
                if turn.get("error_type") or turn["kind"] == "error":
                    raise RuntimeError("Agent operational failure")
                refs = sorted({(r["page_id"], r["section"]) for n in case["nuggets"] for r in n["acceptable_passages"]})
                scores, grade_records = None, []
                for attempt in ((2,) if index == 5 else (1, 2)):
                    evaluate.RUN_DIRECTORY = HERE / "resumption" / f"judge-attempt-{attempt}"
                    output = {**turn, "case_id": key, "trial_index": cell["trial"], "prediction_id": turn["answer_id"], "turns": [turn]}
                    scores = await judge.score(output=output, prompts=[case["query"]], expected_behavior=" ".join(a["description"] for a in case["assertions"]), reference_evidence=[corpora["baseline"].read(p, s).evidence(f"R{i}") for i, (p, s) in enumerate(refs, 1)], minimum_pages=0, require_code=False, assertions=case["assertions"])
                    save(folder / ("score.json" if attempt == 1 else "score-retry.json"), scores)
                    grade_records.append(scores)
                    if attempt == 2:
                        retries.append({"attempt": key, "reason": "Invalid structured grade; identical saved answer and judge contract", "valid_retry": not scores.get("judge_error")})
                    if not scores.get("judge_error"):
                        break
                    if scores["judge_metrics"]["unpriced_calls"] or scores["judge_error"] not in {"ValueError", "ValidationError"}:
                        raise RuntimeError("Judge provider failure")
                if scores.get("judge_error"):
                    raise RuntimeError("Two invalid grades; stop")
                if index == 5:
                    grade_records.insert(0, json.loads((folder / "score.json").read_text()))
                row = {**cell, "attempt": key, "answer_id": turn["answer_id"], "kind": turn["kind"], "passed": scores["passed"], "engine_seconds": turn["elapsed_seconds"], "agent_usd": turn["metrics"]["estimated_usd"], "judge_usd": sum(g["judge_metrics"]["estimated_usd"] for g in grade_records), "judge_attempts": len(grade_records)}
                rows.append(row)
                save(folder / "resumption-budget.json", budget.snapshot())
                print("FINISH", json.dumps(row), flush=True)
            except Exception as exc:
                error = {"attempt": key, "error_type": type(exc).__name__}
                save(folder / "resumption-stopped.json", error)
                break
        completion = {"completed_at": datetime.now(UTC).isoformat(), "status": "complete" if len(rows) == 24 and not error else "incomplete", "planned": 24, "scored": len(rows), "rows": rows, "error": error, "grade_retries": retries, "original_summary": "summary.json", "original_estimated_usd": previous["budget"]["known_estimated_usd"], "resumption_budget": budget.snapshot(), "total_known_estimated_usd": previous["budget"]["known_estimated_usd"] + budget.snapshot()["known_estimated_usd"], "resumption_preparation_seconds": preparation_seconds, "source_sha256": frozen["source_sha256"]}
        save(HERE / "completion.json", completion)
    print("SUMMARY", completion["status"], len(rows), completion["total_known_estimated_usd"], flush=True)
    client.flush()


if __name__ == "__main__":
    asyncio.run(main())
