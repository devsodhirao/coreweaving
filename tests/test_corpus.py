import json

import pytest

from coreweaving.corpus import Corpus, markdown_sections
from coreweaving.evaluate import dataset_rows


def test_fenced_python_comments_remain_in_the_example():
    text = "# Guide\nIntro\n## Example\n```python\n# This is Python\nprint(1)\n```\n## End\nDone"
    sections = markdown_sections(text)
    assert len(sections) == 3
    assert "# This is Python\nprint(1)\n```" in sections[1]


def test_modified_snapshot_is_rejected(tmp_path):
    (tmp_path / "page.md").write_text("changed content")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"pages": [{"collection": "weave", "file": "page.md", "sha256": "wrong"}]})
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        Corpus(tmp_path)


def test_search_finds_distinct_tracing_and_signal_sources():
    corpus = Corpus()
    tracing = corpus.search("conversation turn trace agent", 8)["results"]
    signals = corpus.search("custom signal tag name definition sampling rate", 8)["results"]
    assert any(r["page_id"] == "guides/tracking/trace-agents" for r in tracing)
    assert any(r["page_id"] == "guides/tracking/create-custom-signal" for r in signals)
    assert len(corpus.pages) == len({p.page_id for p in corpus.passages})


def test_evaluation_references_resolve_and_cover_required_categories():
    rows = dataset_rows(Corpus())
    assert len(rows) >= 10
    assert {"multi-hop", "ambiguous", "hallucination-trap", "multi-turn"}.issubset(
        {row["category"] for row in rows}
    )
    assert all(row["reference_evidence"] for row in rows)


def test_legacy_workflow_warning_travels_with_a_later_section():
    passage = Corpus().read("guides/evaluation/custom-monitors", 2).evidence("S1")
    assert "previous approach" in passage["page_context"]
    assert "Signals" in passage["page_context"]
