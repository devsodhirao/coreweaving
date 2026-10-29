import runpy
import uuid
from pathlib import Path

import pytest

compare_records = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/experiments/compare.py")
)["compare_records"]


def record(case, trial, mode, passed, judge_error=None):
    identity = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{case}-{trial}-{mode}"))
    return {
        "case_id": case,
        "trial_index": trial,
        "verify_mode": mode,
        "prediction_id": identity,
        "scores": {
            "passed": passed,
            "judge_error": judge_error,
            "assertions": [{"id": "one", "passed": passed}] if not judge_error else [],
        },
        "output": {
            "prediction_id": identity,
            "elapsed_seconds": 1,
            "trace_url": "https://example.test/",
        },
    }


def test_pairing_and_repeat_reliability_keep_cases_grouped():
    records = [
        record(case, trial, mode, not (mode == "support" and case == "a" and trial == 2))
        for case in ("a", "b")
        for trial in (1, 2)
        for mode in ("support", "support+coverage")
    ]
    result = compare_records(records, 2)
    assert result["arms"]["support"]["passed"] == 3
    assert result["arms"]["support"]["complete_case_groups"] == 2
    assert result["arms"]["support"]["all_trials_passed_cases"] == 1
    assert result["arms"]["support"]["case_mean_standard_error"] == pytest.approx(0.25)
    paired = result["paired_case_trials"]["support vs support+coverage"]
    assert paired == {"both_pass": 3, "both_fail": 0, "right_only_pass": 1, "left_only_pass": 0}


def test_missing_trials_and_judge_errors_are_not_successes_or_valid_pairs():
    result = compare_records(
        [
            record("a", 1, "support", True),
            record("a", 1, "support+coverage", False, "InvalidVerdict"),
        ],
        2,
    )
    assert result["arms"]["support"]["complete_case_groups"] == 0
    assert result["arms"]["support+coverage"]["judge_errors"] == 1
    assert sum(result["paired_case_trials"]["support vs support+coverage"].values()) == 0


def test_duplicate_attempts_require_explicit_reconciliation():
    one = record("a", 1, "support", True)
    with pytest.raises(ValueError, match="Duplicate"):
        compare_records([one, one], 2)


def test_unscored_paid_prediction_remains_in_costs_and_attempts():
    scored = record("a", 1, "support", True)
    pending = {
        "case_id": "b",
        "trial_index": 1,
        "verify_mode": "support",
        "prediction_id": "pending",
        "elapsed_seconds": 3,
        "agent_metrics": {
            "calls": [
                {
                    "purpose": "planner",
                    "estimated_usd": 0.0003,
                    "usage": {"input_tokens": 100, "output_tokens": 10},
                }
            ]
        },
    }
    done = {**scored["output"], **{k: scored[k] for k in ("case_id", "trial_index", "verify_mode")}}
    result = compare_records(
        [scored],
        2,
        [done, pending],
        [done, pending],
        [
            {
                "verify_mode": "support",
                "budget_usage_reconciliation": {
                    "known_estimate_difference_usd": 0.0002,
                    "unpriced_records": 1,
                },
            }
        ],
    )
    arm = result["arms"]["support"]
    assert arm["attempted"] == 2
    assert arm["scored"] == 1
    assert arm["unscored_attempts"] == 1
    assert arm["agent_estimated_usd"] == pytest.approx(0.0003)
    assert arm["total_known_estimated_usd"] == pytest.approx(0.0005)
    assert arm["unpriced_provider_records"] == 1
    assert arm["agent_tokens"]["input_tokens"] == 100
    assert result["cases"]["b"][1]["support"]["passed"] is None
