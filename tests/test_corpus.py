import hashlib
import json
import runpy
from pathlib import Path

import pytest

from coreweaving.corpus import Corpus, markdown_sections
from coreweaving.evaluate import dataset_rows


def local_corpus(tmp_path, pages):
    """Build hash-valid local documents, optionally with redirected canonical URLs."""
    entries = []
    for index, (page_id, text, canonical) in enumerate(pages):
        url = f"https://docs.example.test/weave/{page_id}.md"
        content = text.encode()
        filename = f"page-{index}.md"
        (tmp_path / filename).write_bytes(content)
        entries.append(
            {
                "collection": "weave",
                "file": filename,
                "sha256": hashlib.sha256(content).hexdigest(),
                "url": url,
                "canonical_url": canonical or url.removesuffix(".md"),
                "title": f"Title for {page_id}",
            }
        )
    (tmp_path / "manifest.json").write_text(json.dumps({"pages": entries}))
    return Corpus(tmp_path)


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


def test_reference_sdk_metadata_matches_pinned_source_and_preserves_snapshot():
    directory = Path(__file__).resolve().parents[1] / "data/docs"
    reference_sdk_metadata = runpy.run_path(str(directory.parents[1] / "scripts/fetch_docs.py"))[
        "reference_sdk_metadata"
    ]
    manifest = json.loads((directory / "manifest.json").read_text())
    metadata = reference_sdk_metadata(manifest["pages"], directory)
    assert metadata == {key: manifest[key] for key in metadata}
    corpus = Corpus(directory)
    assert corpus.docs_sdk_version == metadata["reference_sdk_version"] == "0.53.1"
    assert corpus.snapshot_id == "4db7c17b28698bcc2680da22d687f7c4783ecf5e5255e16177b9197e56da14b4"
    assert reference_sdk_metadata([], directory)["reference_sdk_version"] == "unknown"


def test_outgoing_links_resolve_relative_and_snapshot_aliases_once(tmp_path):
    corpus = local_corpus(
        tmp_path,
        [
            (
                "guides/source",
                "# Source\n"
                "[Sibling](target.md#example)\n"
                "[Root](/weave/guides/target?mode=print)\n"
                "[Parent](../guides/target/)\n"
                "[Host alias](https://DOCS.EXAMPLE.TEST:443/weave/guides/target)\n"
                "[Canonical support](/support/weave#help)\n"
                "[Indexed support](../details/support.md)\n"
                "[Self](#source)\n",
                None,
            ),
            ("guides/target", "# Target\nDocumented body.", None),
            ("details/support", "# Support\nHelp.", "https://docs.example.test/support/weave"),
        ],
    )
    assert corpus.outgoing_links("guides/source") == [
        {"page_id": "guides/target", "title": "Title for guides/target"},
        {"page_id": "details/support", "title": "Title for details/support"},
    ]


def test_outgoing_links_use_selected_passage_and_context_without_reading_targets(
    tmp_path, monkeypatch
):
    corpus = local_corpus(
        tmp_path,
        [
            (
                "source",
                "# Source\n[Context](context.md)\n"
                "## Selected\n[Reference][target]\n"
                "## Unread\n[Other](unread.md)\n\n[target]: target.md#details\n",
                None,
            ),
            ("target", "# Target\nTarget facts.", None),
            ("context", "# Context\nContext facts.", None),
            ("unread", "# Unread\nUnread facts.", None),
        ],
    )
    evidence_before = corpus.read("source", 1).evidence("S1")
    calls = []
    read = corpus.read

    def record_read(page_id, section=0):
        calls.append((page_id, section))
        return read(page_id, section)

    monkeypatch.setattr(corpus, "read", record_read)
    assert corpus.outgoing_links("source", 1) == [
        {"page_id": "target", "title": "Title for target"},
        {"page_id": "context", "title": "Title for context"},
    ]
    assert calls == [("source", 1)]
    assert read("source", 1).evidence("S1") == evidence_before


def test_outgoing_links_ignore_code_images_unknown_pages_and_external_hosts(tmp_path):
    corpus = local_corpus(
        tmp_path,
        [
            (
                "source",
                "# Source\n"
                "`[Inline](target.md)`\n\n"
                "```markdown\n[Fenced](target.md)\n```\n\n"
                "    [Indented](target.md)\n\n"
                "![Image](target.md)\n"
                "[Unknown](missing.md)\n"
                "[Foreign](https://elsewhere.test/weave/target.md)\n"
                "[Credentials](https://user@docs.example.test/weave/target.md)\n"
                "[File](file:///weave/target.md)\n"
                "[Script](javascript:target.md)\n"
                "[Malformed](https:target.md)\n"
                "[Missing host](https:///weave/target.md)\n"
                "[Wrong port](https://docs.example.test:0/weave/target.md)\n"
                "[Encoded slash](/weave%2Ftarget.md)\n",
                None,
            ),
            ("target", "# Target\nFacts.", None),
        ],
    )
    assert corpus.outgoing_links("source") == []


def test_outgoing_links_are_bounded_deduplicated_navigation_metadata(tmp_path):
    targets = [f"target-{number}" for number in range(10)]
    text = "# Source\n" + "\n".join(
        f"[Read]({target}.md) [Again]({target}#anchor)" for target in targets
    )
    corpus = local_corpus(
        tmp_path,
        [("source", text, None)] + [(target, "# Target\nFacts.", None) for target in targets],
    )
    assert corpus.outgoing_links("source") == [
        {"page_id": target, "title": f"Title for {target}"} for target in targets[:8]
    ]


def test_outgoing_links_do_not_reinterpret_code_after_section_chunk_boundary(tmp_path):
    content = "# Source\n```markdown\n" + "x" * 7000 + "\n[Code only](target.md)\n```\n"
    corpus = local_corpus(
        tmp_path,
        [("source", content, None), ("target", "# Target\nFacts.", None)],
    )
    assert len(corpus.pages["source"]) == 2
    assert "[Code only]" in corpus.read("source", 1).text
    assert corpus.outgoing_links("source", 1) == []


def test_redirected_relative_links_do_not_choose_between_known_targets(tmp_path):
    corpus = local_corpus(
        tmp_path,
        [
            (
                "guides/source",
                "# Source\n[Ambiguous](target.md)\n",
                "https://docs.example.test/support/source",
            ),
            ("guides/target", "# Guide target\nFacts.", None),
            (
                "details/target",
                "# Support target\nFacts.",
                "https://docs.example.test/support/target",
            ),
        ],
    )
    assert corpus.outgoing_links("guides/source") == []


def test_snapshot_rejects_ambiguous_canonical_aliases(tmp_path):
    with pytest.raises(ValueError, match="Ambiguous document URL alias"):
        local_corpus(
            tmp_path,
            [
                ("first", "# First\nFacts.", "https://docs.example.test/shared/page"),
                ("second", "# Second\nFacts.", "https://docs.example.test:443/shared/page.md#part"),
            ],
        )


@pytest.mark.parametrize("url", ["file:///weave/source", "https:source", "https://[invalid/source"])
def test_snapshot_rejects_malformed_and_non_http_aliases(tmp_path, url):
    with pytest.raises(ValueError, match="Invalid document URL"):
        local_corpus(tmp_path, [("source", "# Source\nFacts.", url)])


def test_signal_overview_exposes_exact_remote_scorer_page_without_body():
    corpus = Corpus()
    links = corpus.outgoing_links("guides/tracking/view-agent-signals")
    assert {
        "page_id": "guides/tracking/remote-scorer-signals",
        "title": "Score agent turns with a remote scorer",
    } in links
    assert all(set(link) == {"page_id", "title"} for link in links)
