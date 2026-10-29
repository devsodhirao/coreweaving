"""Summarize saved paired trials after source-review verdicts; no model calls."""

import hashlib
import json
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from coreweaving.agent import citation_contract, python_syntax_issues
from coreweaving.config import ROOT, redact_sensitive
from coreweaving.corpus import Corpus

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    target = HERE / "comparison.json"
    assert not target.exists(), "Preserve the original report"
    completion = read(HERE / "completion.json")
    assert completion["status"] == "complete" and completion["scored"] == 24
    reviews = {}
    for batch in (1, 2):
        verdict = read(HERE / f"review-verdicts-{batch}.json")
        packet = HERE / f"review-input-{batch}.json"
        assert hashlib.sha256(packet.read_bytes()).hexdigest() == verdict["input_sha256"]
        by_label = {x["label"]: x for x in verdict["rows"]}
        for item in read(HERE / f"review-key-{batch}.json"):
            path = ROOT / item["result"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
            reviews[item["answer_id"]] = by_label[item["label"]]
    corpus = Corpus()
    rows = []
    for row in completion["rows"]:
        folder = HERE / "attempts" / row["attempt"]
        answer = read(folder / "result.json")
        score = read(folder / ("score-retry.json" if (folder / "score-retry.json").exists() else "score.json"))
        sources = []
        for source in answer["all_read_evidence"]:
            if "page_id" not in source:
                continue
            actual = corpus.read(source["page_id"], source["section"])
            sources.append({
                "source_id": source["source_id"], "page_id": source["page_id"], "section": source["section"],
                "raw_text_exact": actual.text == source["text"],
                "stored_text_matches_documented_masking": redact_sensitive(actual.text) == source["text"],
                "credential_redacted": source.get("credential_redacted", False),
                "page_hash_exact": actual.page_sha256 == source["page_sha256"],
            })
        row = {**row, "review": reviews[answer["answer_id"]], "source_checks": sources,
               "assertions_passed": score["assertions_passed"], "assertion_count": score["assertion_count"],
               "research": answer["metrics"]["research"], "provider_calls": answer["metrics"]["model_calls"],
               "tokens": answer["metrics"]["tokens"], "answer_words": len(answer["answer"].split()),
               "audit_calls": sum(c["purpose"] == "verification" for c in answer["metrics"]["calls"]),
               "audit_usd": sum(c["estimated_usd"] for c in answer["metrics"]["calls"] if c["purpose"] == "verification"),
               "queries": [a["input"] for a in answer["actions"] if a["tool"] == "search_docs"],
               "citation_issues": citation_contract(answer["answer"], answer["kind"], answer["source_ids"], {s["source_id"]: s for s in answer["all_read_evidence"]}),
               "python_syntax_issues": python_syntax_issues(answer["answer"])}
        rows.append(row)
    arms = {}
    for arm in ("baseline", "hybrid"):
        subset = [r for r in rows if r["arm"] == arm]
        research = Counter()
        tokens = Counter()
        for r in subset:
            research.update(r["research"])
            tokens.update(r["tokens"])
        arms[arm] = {
            "attempts": len(subset), "judge_passes": sum(r["passed"] for r in subset),
            "source_review_tasks_supported": sum(r["review"]["task_supported"] for r in subset),
            "assertions_passed": sum(r["assertions_passed"] for r in subset), "assertions_planned": sum(r["assertion_count"] for r in subset),
            "agent_usd": round(sum(r["agent_usd"] for r in subset), 8), "judge_usd_including_invalid": round(sum(r["judge_usd"] for r in subset), 8),
            "engine_median_seconds": statistics.median(r["engine_seconds"] for r in subset),
            "engine_mean_seconds": statistics.mean(r["engine_seconds"] for r in subset),
            "engine_range_seconds": [min(r["engine_seconds"] for r in subset), max(r["engine_seconds"] for r in subset)],
            "provider_calls": sum(r["provider_calls"] for r in subset), "audit_calls": sum(r["audit_calls"] for r in subset),
            "audit_usd": sum(r["audit_usd"] for r in subset), "research": dict(research), "tokens": dict(tokens),
        }
    pairs = []
    for case, trial in dict.fromkeys((r["case_id"], r["trial"]) for r in rows):
        b = next(r for r in rows if (r["case_id"], r["trial"], r["arm"]) == (case, trial, "baseline"))
        h = next(r for r in rows if (r["case_id"], r["trial"], r["arm"]) == (case, trial, "hybrid"))
        pairs.append({"case_id": case, "trial": trial,
                      "baseline_attempt": b["attempt"], "hybrid_attempt": h["attempt"],
                      "both_judge_pass": b["passed"] and h["passed"],
                      "both_review_tasks_supported": b["review"]["task_supported"] and h["review"]["task_supported"],
                      "hybrid_minus_baseline_seconds": round(h["engine_seconds"] - b["engine_seconds"], 4),
                      "hybrid_minus_baseline_agent_usd": round(h["agent_usd"] - b["agent_usd"], 8),
                      "hybrid_minus_baseline_searches": h["research"]["searches"] - b["research"]["searches"],
                      "hybrid_minus_baseline_provider_calls": h["provider_calls"] - b["provider_calls"]})
    report = {"created_at": datetime.now(UTC).isoformat(), "source_sha256": completion["source_sha256"],
              "scope": "Six known questions, two repeats per arm. Not held out, not a new full regression, not browser timing or human-calibrated accuracy.",
              "arms": arms, "pairs": pairs, "rows": rows,
              "total_known_estimated_usd": completion["total_known_estimated_usd"],
              "source_checks": {"read_occurrences": sum(len(r["source_checks"]) for r in rows),
                                "masked_occurrences": sum(not s["raw_text_exact"] for r in rows for s in r["source_checks"]),
                                "all_page_hashes_match": all(s["page_hash_exact"] for r in rows for s in r["source_checks"]),
                                "all_stored_text_matches_expected": all(s["stored_text_matches_documented_masking"] for r in rows for s in r["source_checks"]),
                                "citation_issue_count": sum(len(r["citation_issues"]) for r in rows),
                                "python_syntax_issue_count": sum(len(r["python_syntax_issues"]) for r in rows)},
              "paired_counts": {key: {"hybrid_lower": sum(p[key] < 0 for p in pairs), "equal": sum(p[key] == 0 for p in pairs), "hybrid_higher": sum(p[key] > 0 for p in pairs)} for key in ("hybrid_minus_baseline_seconds", "hybrid_minus_baseline_agent_usd", "hybrid_minus_baseline_searches", "hybrid_minus_baseline_provider_calls")}}
    assert abs(sum(a["agent_usd"] + a["judge_usd_including_invalid"] for a in arms.values()) - completion["total_known_estimated_usd"]) < 1e-7
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("arms", "paired_counts", "source_checks", "total_known_estimated_usd")}, indent=2))
    for p in pairs:
        print(json.dumps(p))


if __name__ == "__main__":
    main()
