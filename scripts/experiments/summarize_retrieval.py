"""Summarize saved paired results without calling a model or changing any grade.

Run after the comparison completes. Prints JSON; the original cases remain the
source of truth. Engine time excludes index setup, judging and UI rendering.
"""

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path


def summarize(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    summary = json.loads((directory / "summary.json").read_text())
    records = {}
    hashes = {}
    for path in sorted((directory / "cases").glob("*.json")):
        record = json.loads(path.read_text())
        key = record["case_id"]
        if key in records:
            raise ValueError(f"Duplicate cell: {key}")
        records[key] = record
        hashes[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if summary["status"] != "complete" or set(records) != set(manifest["planned_order"]):
        raise ValueError("A complete, uniquely matched paired run is required")
    cells = []
    for order, key in enumerate(manifest["planned_order"], 1):
        record = records[key]
        output, scores = record["output"], record["scores"]
        metrics, judge = output["metrics"], scores["judge_metrics"]
        if output["source_sha256"] != manifest["source_sha256"] or scores["judge_error"]:
            raise ValueError(f"Invalid runtime or judge result: {key}")
        purposes = Counter(call["purpose"] for call in metrics["calls"])
        cells.append(
            {
                "case_id": key,
                "question_id": output["question_id"],
                "arm": output["retrieval_mode"],
                "order": order,
                "passed": scores["passed"],
                "assertions_passed": scores["assertions_passed"],
                "assertion_count": scores["assertion_count"],
                "engine_seconds": output["elapsed_seconds"],
                "model_calls": metrics["model_calls"],
                "planner_calls": purposes["planner"] + purposes["task_planning"],
                "verification_calls": purposes["verification"],
                "calls_by_purpose": dict(purposes),
                "searches": metrics["research"]["searches"],
                "passage_reads": metrics["research"]["passage_reads"],
                "cache_read_tokens": metrics["tokens"]["cache_read_input_tokens"],
                "cache_write_tokens": metrics["tokens"]["cache_creation_input_tokens"],
                "agent_estimated_usd": metrics["estimated_usd"],
                "judge_estimated_usd": judge["estimated_usd"],
                "trace_id": output["trace_id"],
            }
        )
    arms = {}
    for arm in ("baseline", manifest["candidate"]):
        rows = [row for row in cells if row["arm"] == arm]
        result = {"cases": len(rows), "cases_passed": sum(row["passed"] for row in rows)}
        for key in (
            "assertions_passed",
            "assertion_count",
            "model_calls",
            "planner_calls",
            "verification_calls",
            "searches",
            "passage_reads",
            "cache_read_tokens",
            "cache_write_tokens",
            "agent_estimated_usd",
            "judge_estimated_usd",
        ):
            result[key] = sum(row[key] for row in rows)
        result["median_engine_seconds"] = statistics.median(row["engine_seconds"] for row in rows)
        result["mean_engine_seconds"] = statistics.mean(row["engine_seconds"] for row in rows)
        arms[arm] = result
    pairs = []
    for question_id in manifest["live_case_ids"]:
        pair = {row["arm"]: row for row in cells if row["question_id"] == question_id}
        baseline, candidate = pair["baseline"], pair[manifest["candidate"]]
        pairs.append(
            {
                "question_id": question_id,
                "candidate_minus_baseline_assertions": candidate["assertions_passed"]
                - baseline["assertions_passed"],
                "candidate_minus_baseline_calls": candidate["model_calls"]
                - baseline["model_calls"],
                "candidate_minus_baseline_seconds": candidate["engine_seconds"]
                - baseline["engine_seconds"],
            }
        )
    estimated_usd = sum(row["agent_estimated_usd"] + row["judge_estimated_usd"] for row in cells)
    if abs(estimated_usd - summary["budget"]["estimated_usd"]) > 1e-9:
        raise ValueError("Case costs do not reconcile with the shared budget ledger")
    return {
        "scope": "One trial per arm on six preselected questions; recorded judge grades, not manual correctness. Engine latency excludes setup, judge and UI. Cache/order and sampling variation confound timing; no causal speed claim.",
        "source_sha256": manifest["source_sha256"],
        "dataset_sha256": manifest["dataset_sha256"],
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_case_sha256": hashes,
        "arms": arms,
        "pairs": pairs,
        "cells": cells,
        "total_agent_judge_estimated_usd": estimated_usd,
        "budget_receipt": {k: v for k, v in summary["budget"].items() if k != "calls"},
        "budget_calls": len(summary["budget"]["calls"]),
        "remote_delivery": "See backend-readback.json; local completion does not establish delivery.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(summarize(parser.parse_args().directory), indent=2))
