"""Optional paired experiments; historical aggregation retains retired verifier arms."""

import argparse
import asyncio
import json
import statistics
from collections import defaultdict
from datetime import UTC, datetime

from coreweaving.budget import model_budget
from coreweaving.config import ROOT
from coreweaving.evaluate import VERIFY_MODES, aggregate_records, run_evaluation

# Old evidence remains readable; new runs use only the current runtime modes.
RECORDED_MODES = ("off", "support", "support+coverage")


def compare_records(
    records: list[dict],
    planned_trials: int,
    predictions: list[dict] | None = None,
    attempts: list[dict] | None = None,
    run_receipts: list[dict] | None = None,
) -> dict:
    """Keep repeated trials grouped by case; preserve errors and missing cells."""
    matrix = defaultdict(lambda: defaultdict(dict))
    arms = {}
    predictions = (
        predictions
        if predictions is not None
        else [
            {
                **row["output"],
                **{k: row[k] for k in ("case_id", "trial_index", "verify_mode", "prediction_id")},
            }
            for row in records
        ]
    )
    attempts = attempts if attempts is not None else predictions
    for attempt in attempts:
        key = (attempt["case_id"], attempt["trial_index"], attempt["verify_mode"])
        if key[2] in matrix[key[0]][key[1]]:
            raise ValueError("Duplicate case/trial/mode in attempted comparison.")
        matrix[key[0]][key[1]][key[2]] = {
            "passed": None,
            "judge_error": "No completed score",
            "failed_assertions": [],
            "prediction_id": attempt["prediction_id"],
            "trace_url": attempt.get("trace_url"),
        }
    scored_keys = set()
    for record in records:
        key = (record["case_id"], record["trial_index"], record["verify_mode"])
        cell = matrix[key[0]][key[1]]
        if key in scored_keys:
            raise ValueError("Duplicate case/trial/mode in comparison.")
        scored_keys.add(key)
        cell[key[2]] = {
            "passed": record["scores"]["passed"],
            "judge_error": record["scores"].get("judge_error"),
            "failed_assertions": [
                x["id"] for x in record["scores"].get("assertions", []) if not x["passed"]
            ],
            "prediction_id": record["prediction_id"],
            "trace_url": record["output"].get("trace_url"),
        }
    for mode in RECORDED_MODES:
        selected = [record for record in records if record["verify_mode"] == mode]
        attempted = [row for row in attempts if row["verify_mode"] == mode]
        outputs = [row for row in predictions if row["verify_mode"] == mode]
        receipts = [row for row in (run_receipts or []) if row["verify_mode"] == mode]
        by_case = defaultdict(list)
        for record in selected:
            by_case[record["case_id"]].append(record)
        case_means = [
            statistics.mean(int(row["scores"]["passed"]) for row in rows)
            for rows in by_case.values()
            if len(rows) == planned_trials and not any(r["scores"].get("judge_error") for r in rows)
        ]
        assertions = [x for row in selected for x in row["scores"].get("assertions", [])]
        aggregation = aggregate_records(outputs, selected)
        # A provider response can precede a persisted turn/judge receipt. Keep its
        # known charge separate instead of silently calling a partial arm cheaper.
        unreconciled = sum(
            row.get("budget_usage_reconciliation", {}).get("known_estimate_difference_usd", 0)
            for row in receipts
        )
        arms[mode] = {
            "attempted": len(attempted),
            "scored": len(selected),
            "unscored_attempts": len(attempted) - len(selected),
            "passed": sum(row["scores"]["passed"] for row in selected),
            "judge_errors": sum(bool(row["scores"].get("judge_error")) for row in selected),
            "assertions_assessed": len(assertions),
            "assertions_passed": sum(x["passed"] for x in assertions),
            "complete_case_groups": len(case_means),
            "all_trials_passed_cases": sum(value == 1 for value in case_means),
            "case_mean_standard_error": (
                statistics.stdev(case_means) / len(case_means) ** 0.5
                if len(case_means) > 1
                else None
            ),
            "agent_estimated_usd": aggregation["usage"]["agent"]["known_estimated_usd"],
            "judge_estimated_usd": aggregation["usage"]["judge"]["known_estimated_usd"],
            "unpriced_calls": aggregation["usage"]["combined"]["unpriced_calls"],
            "known_estimated_usd_without_completed_receipt": round(unreconciled, 8),
            "total_known_estimated_usd": round(
                aggregation["usage"]["combined"]["known_estimated_usd"] + unreconciled, 8
            ),
            "unpriced_provider_records": sum(
                row.get("budget_usage_reconciliation", {}).get("unpriced_records", 0)
                for row in receipts
            ),
            "mean_case_latency_seconds": (
                statistics.mean(
                    sum(t.get("elapsed_seconds", 0) for t in r.get("turns", [r])) for r in outputs
                )
                if outputs
                else None
            ),
            "agent_tokens": aggregation["usage"]["agent"]["tokens"],
        }
    paired = {}
    for left, right in (("off", "support"), ("support", "support+coverage")):
        counts = {"both_pass": 0, "both_fail": 0, "right_only_pass": 0, "left_only_pass": 0}
        for trials in matrix.values():
            for cells in trials.values():
                if left not in cells or right not in cells:
                    continue
                if cells[left]["judge_error"] or cells[right]["judge_error"]:
                    continue
                a, b = cells[left]["passed"], cells[right]["passed"]
                key = (
                    "both_pass"
                    if a and b
                    else "both_fail"
                    if not a and not b
                    else ("right_only_pass" if b else "left_only_pass")
                )
                counts[key] += 1
        paired[left + " vs " + right] = counts
    return {
        "arms": arms,
        "paired_case_trials": paired,
        "cases": {case: dict(trials) for case, trials in matrix.items()},
        "interpretation_limit": (
            "Small selected-case pilot, not a population reliability estimate. Repeated trials "
            "remain grouped by case. SE describes variation across complete case means only. "
            "Report paired outcomes and inspect failures; do not select a winner from noise. "
            "Coverage mode changes evidence breadth as well as the coverage policy."
        ),
    }


async def run_comparison(name: str, budget_usd: float = 10, trials: int = 2) -> dict:
    if not name or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in name
    ):
        raise ValueError("Comparison name must contain only letters, numbers, '-' and '_'.")
    if trials not in (1, 2, 3):
        raise ValueError("This bounded comparison supports one to three trials.")
    directory = ROOT / "results" / name
    directory.mkdir(parents=True, exist_ok=False)
    runs, records, predictions, attempts, stop = [], [], [], [], None
    with model_budget(budget_usd) as budget:
        for trial in range(trials):
            # Rotate the arm order across repeats, with the same shuffled cases
            # within every arm. It reduces fixed-order bias, not all cache effects.
            offset = trial % len(VERIFY_MODES)
            order = VERIFY_MODES[offset:] + VERIFY_MODES[:offset]
            for mode in order:
                label = mode.replace("+", "-")
                run_name = f"{name}-{label}-t{trial + 1}"
                result = await run_evaluation(
                    argparse.Namespace(
                        name=run_name,
                        suite="capability",
                        verify_mode=mode,
                        trials=1,
                        trial_offset=trial,
                        budget_usd=budget_usd,
                        seed=20261026 + trial,
                        only=None,
                    )
                )
                runs.append(
                    {
                        k: result.get(k)
                        for k in (
                            "run",
                            "verify_mode",
                            "trial_offset",
                            "status",
                            "evaluation_url",
                            "evaluation_call_id",
                            "dataset_ref",
                            "source_sha256",
                            "dataset_sha256",
                            "remote_sync",
                            "passed",
                            "completed_cases",
                            "run_error",
                            "budget_usage_reconciliation",
                        )
                    }
                )
                records.extend(
                    json.loads(path.read_text())
                    for path in sorted((ROOT / "results" / run_name / "cases").glob("*.json"))
                )
                predictions.extend(
                    json.loads(path.read_text())
                    for folder in ("predictions", "prediction-errors")
                    for path in sorted((ROOT / "results" / run_name / folder).glob("*.json"))
                )
                attempts.extend(
                    json.loads(path.read_text())
                    for path in sorted((ROOT / "results" / run_name / "attempts").glob("*.json"))
                )
                if result["status"] != "complete" or budget.snapshot()["stopped_reason"]:
                    stop = "Stopped after an incomplete run, judge/provider error, or budget limit."
                summary = {
                    "name": name,
                    "created_at": datetime.now(UTC).isoformat(),
                    "planned_case_trials": 6 * len(VERIFY_MODES) * trials,
                    "planned_trials_per_case": trials,
                    "runs": runs,
                    "stop_reason": stop,
                    "budget": budget.snapshot(),
                    **compare_records(records, trials, predictions, attempts, runs),
                }
                (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
                if stop:
                    break
            if stop:
                break
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--budget-usd", type=float, default=10)
    parser.add_argument("--trials", type=int, default=2)
    args = parser.parse_args()
    result = asyncio.run(run_comparison(args.name, args.budget_usd, args.trials))
    print(json.dumps({"arms": result["arms"], "stop_reason": result["stop_reason"]}, indent=2))


if __name__ == "__main__":
    main()
