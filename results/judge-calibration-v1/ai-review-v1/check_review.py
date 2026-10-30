"""Recheck this saved AI review offline; no inference or Weave writes.

Run from the repository root with:
uv run python results/judge-calibration-v1/ai-review-v1/check_review.py --output /tmp/ai-review-checks.json
"""

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from markdown_it import MarkdownIt

from coreweaving.config import redact_sensitive, source_fingerprint
from coreweaving.corpus import Corpus

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
QUALITIES = ("correctness", "completeness", "grounding", "uncertainty")
REVIEW_SHA = "9b3f34485a7a4e44c1831f5d0bbc2ff485e15c43c726ac87aa7c80bcde33c008"
APPROVED_STDLIB_EXAMPLES = {
    "c59d0a18a62e5c199b538cce967930fd8e78eb021fadaaf44b5864aaa2db713e",
    "3ee3464e3584d4e41a6a141f6c0526ee1dc030d53ae8f5c57e7453d5a7fa4173",
}


def read(path):
    return json.loads(path.read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True).encode())


def field_at(value, pointer):
    for part in pointer.strip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def content_for(entry):
    case = read(ROOT / entry["record"])
    row = next(x for x in read(ROOT / entry["dataset"])
               if x["example_id"] == entry["example_id"])
    output = case["output"]
    return {
        "prompts": row["prompts"],
        "conversation_context": output.get("conversation_context", []),
        "answer": output["answer"],
        "expected_behavior": row["expected_behavior"],
        "assertions": row["assertions"],
        "reference_evidence": row["reference_evidence"],
        "sources": output["sources"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output file; keep prior receipts.")
    assert sha((HERE / "review.json").read_bytes()) == REVIEW_SHA
    review = read(HERE / "review.json")
    selected = read(HERE.parent / "selection.json")
    assert digest(selected) == review["selection_sha256"]
    selected = {x["sample_id"]: x for x in selected}
    key = {x["sample_id"]: x for x in read(HERE.parent / "judge-key.json")}
    corpus = Corpus()
    markdown = MarkdownIt("commonmark", {"html": False})
    source_checks, quote_checks, syntax_checks, replays = [], [], [], []
    seen_ids = set()
    for item in review["items"]:
        sample = item["sample_id"]
        assert sample not in seen_ids
        seen_ids.add(sample)
        entry = selected[sample]
        for field in ("record", "dataset", "manifest"):
            assert sha((ROOT / entry[field]).read_bytes()) == entry[field + "_sha256"]
        content = content_for(entry)
        assert digest(content) == item["review_content_sha256"] == entry["review_content_sha256"]
        assert sha(content["answer"].encode()) == item["answer_sha256"]
        assert set(item["ai_labels"]) == set(QUALITIES)
        assert "human_labels" not in item
        evidence_ids = {p["id"] for p in item["evidence"]}
        for label in item["ai_labels"].values():
            assert type(label["passed"]) is bool and label["reason"].strip()
            assert set(label["evidence_ids"]) <= evidence_ids
            assert label["evidence_ids"]
        assert item["all_four_qualities_pass"] == all(
            v["passed"] for v in item["ai_labels"].values())
        assert item["sources_consulted_by_original_answer"] == len(content["sources"])
        for proof in item["evidence"]:
            text = field_at(content, proof["content_pointer"])
            assert sha(text.encode()) == proof["field_sha256"]
            assert text[proof["start"]:proof["end"]] == proof["quote"]
            quote_checks.append({"sample_id": sample, "evidence_id": proof["id"],
                                 "exact_quote_matches": True})
        for collection in ("sources", "reference_evidence"):
            for index, evidence in enumerate(content[collection]):
                if "page_id" not in evidence:
                    continue
                saved = asdict(corpus.read(evidence["page_id"], evidence["section"]))
                assert evidence["page_sha256"] == saved["page_sha256"]
                match = {}
                for field in ("text", "page_context"):
                    if field in evidence:
                        raw = saved[field]
                        assert evidence[field] in (raw, redact_sensitive(raw)), (
                            sample, collection, index, field)
                        match[field] = "exact" if evidence[field] == raw else "credential masking"
                source_checks.append({"sample_id": sample, "collection": collection,
                                      "index": index, "page_id": evidence["page_id"],
                                      "section": evidence["section"], "matches": match})
        for number, block in enumerate(markdown.parse(content["answer"])):
            if block.type == "fence" and block.info.lower().split()[:1] in (
                ["python"], ["py"], ["python3"]
            ):
                ast.parse(block.content)
                syntax_checks.append({"sample_id": sample, "block": number, "parses": True})
        for evidence in content["sources"]:
            if "code" not in evidence:
                continue
            code_hash = sha(evidence["code"].encode())
            assert code_hash in APPROVED_STDLIB_EXAMPLES
            result = subprocess.run(
                [sys.executable, "-I", "-c", evidence["code"]],
                capture_output=True, text=True, timeout=5, env={}, check=False,
            )
            assert result.returncode == evidence["exit_code"] == 0
            assert result.stdout == evidence["output"] and not result.stderr
            replays.append({"sample_id": sample, "code_sha256": code_hash,
                            "output": result.stdout, "exit_code": result.returncode,
                            "matches_saved_result": True,
                            "scope": "New isolated stdlib calculation; no agent or SDK replay."})
    assert seen_ids == set(selected) and len(seen_ids) == 30
    agreement, disagreements = {}, []
    for quality in QUALITIES:
        pairs = Counter((key[x["sample_id"]]["judge_labels"][quality],
                         x["ai_labels"][quality]["passed"]) for x in review["items"])
        agreement[quality] = {
            "original_pass_review_pass": pairs[True, True],
            "original_fail_review_fail": pairs[False, False],
            "original_pass_review_fail": pairs[True, False],
            "original_fail_review_pass": pairs[False, True],
            "agree": pairs[True, True] + pairs[False, False], "total": 30,
        }
    for item in review["items"]:
        original = key[item["sample_id"]]
        differences = [q for q in QUALITIES
                       if original["judge_labels"][q] != item["ai_labels"][q]["passed"]]
        if differences:
            disagreements.append({"sample_id": item["sample_id"], "qualities": differences,
                                  "original_labels": original["judge_labels"],
                                  "review_labels": {q: v["passed"] for q, v in item["ai_labels"].items()},
                                  "original_explanation": original["original_judge_explanation"]})
    report = {
        "checked_at": datetime.now(UTC).isoformat(), "review_sha256": REVIEW_SHA,
        "runtime_source_sha256": source_fingerprint(), "corpus_snapshot_id": corpus.snapshot_id,
        "summary": {
            "saved_answers_verified": len(seen_ids), "ai_labels_filled": 120,
            "exact_evidence_quotes_verified": len(quote_checks),
            "source_and_reference_occurrences_verified": len(source_checks),
            "python_blocks_syntax_checked": len(syntax_checks),
            "stdlib_replays_matching_saved_output": len(replays),
            "all_four_quality_passes": sum(x["all_four_qualities_pass"] for x in review["items"]),
            "answers_with_a_failed_quality": sum(not x["all_four_qualities_pass"] for x in review["items"]),
            "rubric_sensitive_flagged_answers": sum(x["rubric_sensitive"] for x in review["items"]),
        },
        "model_agreement_only": agreement, "disagreements": disagreements,
        "source_checks": source_checks, "quote_checks": quote_checks,
        "syntax_checks": syntax_checks, "stdlib_replays": replays,
        "limits": [
            "Exact quotes and document hashes prove provenance, not semantic truth.",
            "Agreement compares two AI interpretations, not AI against humans.",
            "No live SDK/provider execution, new regression, inference call or remote annotation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(agreement, indent=2))


if __name__ == "__main__":
    main()
