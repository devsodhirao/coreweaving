"""Offline diagnostic; reuse pinned local vectors, never call a generative API.

From the repository root, with the original local model and vector cache present:
uv run --offline --frozen --with fastembed==0.9.1 python -m results.retrieval-followup-v2.replay
Uses exclusive output creation: keep completed receipts and use a new directory
for any different instrument. App code, lockfile and old results are unchanged.
"""

import hashlib
import json
import statistics
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from coreweaving.config import ROOT, source_fingerprint
from scripts.experiments.retrieval_backend import ExperimentalCorpus, PinnedFastEmbed, digest
from scripts.experiments.retrieval_compare import nugget_metrics

HERE = Path(__file__).resolve().parent
OLD = ROOT / "results/retrieval-comparison-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


class CachedHybrid(ExperimentalCorpus):
    """Only reuse embeddings of exactly the same ordered text with the same encoder."""

    def _vectors(self, windows, cache_dir):
        old_identity = json.loads((OLD / "offline-hybrid.json").read_text())["arm"]["identity"]
        keys = ("snapshot_id", "index_sha256", "windows_sha256", "embedding")
        for key in keys:
            if self.identity[key] != old_identity[key]:
                raise ValueError(f"Existing vectors cannot be reused: {key} differs")
        old_key = digest(old_identity)
        path = Path(cache_dir) / f"{old_key}.npz"
        with np.load(path, allow_pickle=False) as cached:
            values = cached["vectors"]
            if str(cached["key"]) != old_key:
                raise ValueError("Cache identity differs")
            if str(cached["sha256"]) != hashlib.sha256(values.tobytes()).hexdigest():
                raise ValueError("Cache checksum differs")
            if values.shape != (len(windows), self.embedder.dimension):
                raise ValueError("Cache shape differs")
            if not np.isfinite(values).all() or not np.allclose(
                np.linalg.norm(values, axis=1), 1, atol=1e-5
            ):
                raise ValueError("Invalid cached vectors")
        self.cache_hit = True
        self.cache_receipt = {"file": path.name, "sha256": sha(path), "matched_fields": keys}
        return values


def measures(case, hits, corpus):
    selected = nugget_metrics(case, hits)
    pages = {h["page_id"] for h in hits}
    passages = [corpus.read(h["page_id"], h["section"]) for h in hits]
    reachable, exposed = [], []
    for nugget in case["nuggets"]:
        refs = nugget["acceptable_passages"]
        if any(ref["page_id"] in pages for ref in refs):
            reachable.append(nugget["id"])
        if any(
            ref["quote"] in p.text or ref["quote"] in p.page_context
            for p in passages
            for ref in refs
        ):
            exposed.append(nugget["id"])
    return {
        "selected": selected,
        "reference_page_reachable": reachable,
        "exact_quote_exposed_if_hits_read": exposed,
        "returned_text_chars": sum(len(json.dumps(h)) for h in hits),
    }


def main():
    data = json.loads((HERE / "cases.json").read_text())
    baseline = ExperimentalCorpus(mode="baseline")
    if source_fingerprint() != data["runtime_source_sha256"]:
        raise ValueError("Runtime differs from frozen cases")
    if baseline.snapshot_id != data["snapshot_id"]:
        raise ValueError("Snapshot differs")
    for case in data["cases"]:
        for nugget in case["nuggets"]:
            for ref in nugget["acceptable_passages"]:
                if ref["quote"] not in baseline.read(ref["page_id"], ref["section"]).text:
                    raise ValueError("Reference quote differs")
    hybrid = CachedHybrid(
        mode="hybrid",
        embedder=PinnedFastEmbed(ROOT / ".agent-cache/bge-small-pinned"),
        cache_dir=ROOT / ".agent-cache/retrieval-index",
    )
    freeze = {
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "runtime_source_sha256": source_fingerprint(),
        "cases_sha256": sha(HERE / "cases.json"),
        "protocol_sha256": sha(HERE / "protocol.md"),
        "runner_sha256": sha(Path(__file__)),
        "baseline": baseline.identity,
        "hybrid": hybrid.identity,
        "vector_cache": hybrid.cache_receipt,
        "paid_calls": 0,
    }
    save("freeze.json", freeze)
    rows = []
    for case in data["cases"]:
        for arm, corpus, limit in (
            ("bm25_6", baseline, 6), ("bm25_8", baseline, 8), ("hybrid_6", hybrid, 6)
        ):
            hits = corpus.search(case["query"], limit=limit)["results"]
            rows.append({
                "case_id": case["id"], "selection": case["selection"], "arm": arm,
                "hits": hits, **measures(case, hits, corpus),
            })
    summary = {
        arm: {
            "selected_source_recall": statistics.mean(
                r["selected"]["nugget_recall"] for r in rows if r["arm"] == arm
            ),
            "all_selected_sources_found": sum(
                r["selected"]["all_nuggets"] for r in rows if r["arm"] == arm
            ),
        }
        for arm in ("bm25_6", "bm25_8", "hybrid_6")
    }
    save("offline.json", {"status": "complete", "freeze": freeze, "rows": rows, "summary": summary})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
