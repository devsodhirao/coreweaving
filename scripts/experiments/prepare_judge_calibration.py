"""Freeze saved answers for owner labeling; no provider calls or remote writes."""

import argparse
import ast
import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_RUN = "presentation-regression-retry-v1"
RUBRIC_VERSION = "2.3-task-aligned-assertions"
SEED = 20261030
QUALITIES = ("correctness", "completeness", "grounding", "uncertainty")


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rubric(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "RUBRIC" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("Missing judge instructions")


def candidate_pool():
    """Use the current rubric, judge model and exact judge instructions."""
    current_rubric = rubric((ROOT / "src/coreweaving/evaluate.py").read_text())
    candidates, inventory = [], []
    for path in sorted((ROOT / "results").glob("*/manifest.json")):
        manifest = read(path)
        if manifest.get("rubric_version") != RUBRIC_VERSION:
            continue
        source = subprocess.check_output(
            ["git", "show", manifest["git_commit"] + ":src/coreweaving/evaluate.py"],
            cwd=ROOT,
            text=True,
        )
        if rubric(source) != current_rubric or manifest["judge_model"] != "claude-opus-5-5":
            continue
        dataset_path = path.parent / "dataset.json"
        rows = {row["example_id"]: row for row in read(dataset_path)}
        eligible, ungraded = [], []
        for case_path in sorted(path.parent.glob("cases/*.json")):
            case = read(case_path)
            scores = case["scores"]
            if scores.get("judge_error") or not all(
                type(scores.get(key)) is int and 0 <= scores[key] <= 4 for key in QUALITIES
            ):
                ungraded.append(case_path.name)
                continue
            row = rows[case["example_id"]]
            assert {a["id"] for a in scores["assertions"]} == {
                a["id"] for a in row["assertions"]
            }
            entry = {
                "record": str(case_path.relative_to(ROOT)),
                "record_sha256": file_hash(case_path),
                "manifest": str(path.relative_to(ROOT)),
                "manifest_sha256": file_hash(path),
                "dataset": str(dataset_path.relative_to(ROOT)),
                "dataset_sha256": file_hash(dataset_path),
                "case_id": case["case_id"],
                "example_id": case["example_id"],
                "prediction_id": case["prediction_id"],
                "category": row["category"],
                "source_sha256": manifest["source_sha256"],
                "predict_and_score_call_id": case["output"]["predict_and_score_call_id"],
                "answer_sha256": hashlib.sha256(case["output"]["answer"].encode()).hexdigest(),
                "trace_url": case["output"]["trace_url"],
                "judge_passed": scores["passed"],
            }
            eligible.append(entry)
        inventory.append({
            "run": path.parent.name,
            "eligible": len(eligible),
            "failed": sum(not e["judge_passed"] for e in eligible),
            "ungraded_records_excluded": ungraded,
        })
        candidates.extend(eligible)
    assert len({e["prediction_id"] for e in candidates}) == len(candidates)
    return candidates, inventory, current_rubric


def select(candidates):
    required = [e for e in candidates if not e["judge_passed"]
                or f"/{CURRENT_RUN}/" in e["record"]
                or "/essence-regression-v2-resume/" in e["record"]]
    selected = {e["prediction_id"]: e for e in required}
    assert len(selected) <= 30
    counts = Counter(e["category"] for e in selected.values())
    while len(selected) < 30:
        remaining = [e for e in candidates if e["prediction_id"] not in selected]
        choice = min(remaining, key=lambda e: (
            counts[e["category"]], digest([SEED, "sample", e["record"]])
        ))
        selected[choice["prediction_id"]] = choice
        counts[choice["category"]] += 1
    return sorted(selected.values(), key=lambda e: digest([SEED, "order", e["record"]]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.private_output.exists():
        parser.error("Use new directories; never overwrite frozen records or human labels.")
    if args.private_output.resolve().is_relative_to(ROOT):
        parser.error("Keep the owner's labeling files outside the repository.")
    pool, inventory, instructions = candidate_pool()
    chosen = select(pool)
    assert len(chosen) == 30
    selected_ids = {e["prediction_id"] for e in chosen}
    assert all(e["prediction_id"] in selected_ids for e in pool if not e["judge_passed"])
    packet, key = [], []
    for i, entry in enumerate(chosen, 1):
        entry["sample_id"] = f"J{i:02d}"
        case = read(ROOT / entry["record"])
        row = next(r for r in read(ROOT / entry["dataset"])
                   if r["example_id"] == entry["example_id"])
        output = case["output"]
        content = {
            "prompts": row["prompts"],
            "conversation_context": output.get("conversation_context", []),
            "answer": output["answer"],
            "expected_behavior": row["expected_behavior"],
            "assertions": row["assertions"],
            "reference_evidence": row["reference_evidence"],
            "sources": output["sources"],
        }
        entry["review_content_sha256"] = digest(content)
        packet.append({
            "sample_id": entry["sample_id"], "content": content,
            "human_labels": {q: {"passed": None, "reason": ""} for q in QUALITIES},
        })
        key.append({
            "sample_id": entry["sample_id"],
            "judge_scores": {q: case["scores"][q] for q in QUALITIES},
            "judge_labels": {q: case["scores"][q] >= 3 for q in QUALITIES},
            "judge_case_passed": entry.pop("judge_passed"),
            "original_judge_explanation": case["scores"]["explanation"],
        })
    args.output.mkdir(parents=True)
    args.private_output.mkdir(parents=True)
    protocol = {
        "created_at": datetime.now(UTC).isoformat(), "seed": SEED,
        "rubric_version": RUBRIC_VERSION, "judge_model": "claude-opus-5-5",
        "judge_instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
        "sampling": "All valid failures under the current rubric/instructions/model, all 13 current "
        "cases, the documented disputed hierarchy pass, then category-balanced seeded passes.",
        "population": inventory,
        "eligible_count": len(pool), "selected_count": len(chosen),
        "selected_categories": dict(sorted(Counter(e['category'] for e in chosen).items())),
        "selected_judge_failures": sum(not e["judge_case_passed"] for e in key),
        "selection_sha256": digest(chosen),
        "quality_threshold": "pass = original score >= 3; fail = score <= 2",
        "unit": "Final evaluated answer in full conversation context; one unit per prediction, "
        "not one independent grade for each turn of a multi-turn case.",
        "model_calls": 0, "new_model_cost_usd": 0,
        "human_labels_supplied": 0, "agreement_status": "waiting for owner labels",
        "limits": [
            "Development answers across runtime versions; not current-runtime prevalence.",
            "Failures and known disagreement are oversampled; raw agreement is sample-specific.",
            "Owner knows the app; hidden grades do not make this an independent blinded study.",
            "The four dimensions do not independently calibrate every assertion or integrity gate.",
            "No second-family scoring or agent reruns until after the owner handoff.",
        ],
    }
    for name, value in [("protocol.json", protocol), ("selection.json", chosen),
                        ("judge-key.json", key)]:
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n")
    (args.private_output / "labels.json").write_text(json.dumps({
        "selection_sha256": protocol["selection_sha256"],
        "annotator": None, "items": packet,
    }, indent=2) + "\n")
    print(json.dumps({k: protocol[k] for k in [
        "eligible_count", "selected_count", "selected_categories", "selected_judge_failures"
    ]}, indent=2))


if __name__ == "__main__":
    main()
