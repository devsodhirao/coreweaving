"""Run the frozen current-agent comparison with existing retrieval/judge code.

uv run --offline --frozen --with fastembed==0.9.1 python -m results.retrieval-live-v3.run
No runtime defaults or completed result files are changed.
"""

import asyncio
import hashlib
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

HERE = Path(__file__).resolve().parent
CASES = ROOT / "results/retrieval-followup-v2/cases.json"
BACKEND = ROOT / "scripts/experiments/retrieval_backend.py"
REUSE = ROOT / "results/retrieval-followup-v2/replay.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


async def main():
    if (HERE / "freeze.json").exists():
        raise FileExistsError("Preserve the prior run; this runner does not resume or overwrite")
    spec = importlib.util.spec_from_file_location("reuse_hybrid", REUSE)
    reuse = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reuse)
    data = json.loads(CASES.read_text())
    cfg = settings()
    assert cfg.verify_mode == "support"
    corpora, preparation = {}, {}
    for arm in ("baseline", "hybrid"):
        start = time.monotonic()
        corpora[arm] = Corpus() if arm == "baseline" else reuse.CachedHybrid(
            mode="hybrid",
            embedder=PinnedFastEmbed(ROOT / ".agent-cache/bge-small-pinned"),
            cache_dir=ROOT / ".agent-cache/retrieval-index",
        )
        preparation[arm] = time.monotonic() - start
        assert corpora[arm].snapshot_id == data["snapshot_id"]
    offline = json.loads((CASES.parent / "offline.json").read_text())
    for case in data["cases"]:
        for nugget in case["nuggets"]:
            for ref in nugget["acceptable_passages"]:
                assert ref["quote"] in corpora["baseline"].read(ref["page_id"], ref["section"]).text
        for arm, old_arm in (("baseline", "bm25_6"), ("hybrid", "hybrid_6")):
            prior = next(r["hits"] for r in offline["rows"] if r["case_id"] == case["id"] and r["arm"] == old_arm)
            current = corpora[arm].search(case["query"])["results"]
            assert [(r["page_id"], r["section"]) for r in prior] == [(r["page_id"], r["section"]) for r in current]
    order = [
        {"case_id": case["id"], "trial": trial, "arm": arm}
        for trial in (1, 2)
        for index, case in enumerate(data["cases"])
        for arm in (("baseline", "hybrid") if (index + trial) % 2 else ("hybrid", "baseline"))
    ]
    frozen = {
        "created_at": datetime.now(UTC).isoformat(),
        "source_sha256": source_fingerprint(),
        "cases_sha256": sha(CASES), "protocol_sha256": sha(HERE / "protocol.md"),
        "runner_sha256": sha(Path(__file__)), "backend_sha256": sha(BACKEND),
        "reuse_helper_sha256": sha(REUSE), "settings": asdict(cfg),
        "preparation_seconds_with_existing_vectors": preparation,
        "hybrid_identity": corpora["hybrid"].identity,
        "vector_cache": corpora["hybrid"].cache_receipt,
        "raw_rankings_match_prior_offline": True,
        "planned_order": order, "estimated_budget_usd": 20,
        "writer_checker_effort": "medium", "judge_effort": "provider_default",
        "judge_cache_enabled": False,
    }
    save(HERE / "freeze.json", frozen)
    client = init_weave()
    judge = evaluate.QualityJudge(name="retrieval-live-v3-quality", judge_model=cfg.judge_model)
    evaluate.RUN_DIRECTORY = HERE
    rows, error = [], None
    with model_budget(20) as budget:
        for index, cell in enumerate(order, 1):
            case = next(c for c in data["cases"] if c["id"] == cell["case_id"])
            key = f"{index:02d}-{cell['case_id']}--t{cell['trial']}--{cell['arm']}"
            print("START", key, flush=True)
            folder = HERE / "attempts" / key
            folder.mkdir(parents=True, exist_ok=False)
            try:
                assert source_fingerprint() == frozen["source_sha256"]
                assert sha(CASES) == frozen["cases_sha256"] and sha(BACKEND) == frozen["backend_sha256"]
                save(folder / "submission.json", {**cell, "submitted_at": datetime.now(UTC).isoformat(), "query": case["query"]})
                turn = await asyncio.to_thread(
                    Agent(corpora[cell["arm"]], cfg).run, case["query"], Session(),
                    eval_attributes={"coreweaving.experiment": "retrieval-live-v3", "coreweaving.retrieval_mode": cell["arm"], "coreweaving.case_id": case["id"], "coreweaving.trial": cell["trial"]},
                )
                save(folder / "result.json", turn)
                assert turn["source_sha256"] == frozen["source_sha256"]
                if turn.get("error_type") or turn["kind"] == "error":
                    raise RuntimeError("Agent operational failure; preserve it and stop")
                refs = sorted({(r["page_id"], r["section"]) for n in case["nuggets"] for r in n["acceptable_passages"]})
                output = {**turn, "case_id": key, "trial_index": cell["trial"], "prediction_id": turn["answer_id"], "turns": [turn]}
                scores = await judge.score(
                    output=output, prompts=[case["query"]],
                    expected_behavior=" ".join(a["description"] for a in case["assertions"]),
                    reference_evidence=[corpora["baseline"].read(p, s).evidence(f"R{i}") for i, (p, s) in enumerate(refs, 1)],
                    minimum_pages=0, require_code=False, assertions=case["assertions"],
                )
                save(folder / "score.json", scores)
                if scores.get("judge_error"):
                    raise RuntimeError("Judge delivery failure; preserve it and stop")
                row = {**cell, "attempt": key, "answer_id": turn["answer_id"], "kind": turn["kind"], "passed": scores["passed"], "engine_seconds": turn["elapsed_seconds"], "agent_usd": turn["metrics"]["estimated_usd"], "judge_usd": scores["judge_metrics"]["estimated_usd"]}
                rows.append(row)
                print("FINISH", json.dumps(row), flush=True)
                save(folder / "budget.json", budget.snapshot())
            except Exception as exc:
                error = {"attempt": key, "error_type": type(exc).__name__}
                save(folder / "stopped.json", error)
                break
        summary = {"completed_at": datetime.now(UTC).isoformat(), "status": "complete" if len(rows) == 24 and not error else "incomplete", "planned": 24, "scored": len(rows), "rows": rows, "error": error, "budget": budget.snapshot(), "source_sha256": frozen["source_sha256"]}
        save(HERE / "summary.json", summary)
    print("SUMMARY", summary["status"], len(rows), budget.snapshot()["known_estimated_usd"], flush=True)
    client.flush()


if __name__ == "__main__":
    asyncio.run(main())
