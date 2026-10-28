import hashlib
import json
import re
import runpy
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from coreweaving.corpus import Corpus

backend = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/experiments/retrieval_backend.py")
)
ExperimentalCorpus = backend["ExperimentalCorpus"]
reciprocal_rank_fusion = backend["reciprocal_rank_fusion"]
source_contexts = backend["source_contexts"]
token_windows = backend["token_windows"]


def snapshot(directory, documents):
    directory.mkdir(exist_ok=True)
    pages = []
    for index, (title, text) in enumerate(documents):
        name = f"page-{index}.md"
        content = text.encode()
        (directory / name).write_bytes(content)
        pages.append(
            {
                "collection": "weave",
                "file": name,
                "title": title,
                "url": f"https://docs.example.test/weave/page-{index}.md",
                "canonical_url": f"https://docs.example.test/weave/page-{index}",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    (directory / "manifest.json").write_text(json.dumps({"pages": pages}))
    return directory


class WordTokenizer:
    def encode(self, text, add_special_tokens=True):
        spans = list(re.finditer(r"\S+", text))
        return SimpleNamespace(
            offsets=[match.span() for match in spans],
            ids=list(range(len(spans) + (2 if add_special_tokens else 0))),
        )


class FakeEmbedder:
    dimension = 3

    def __init__(self, revision="first"):
        self.identity = {"model": "deterministic-test-only", "revision": revision}
        self.document_calls = []
        self.query_calls = []

    def windows(self, text):
        return token_windows(text, WordTokenizer(), width=12, overlap=3)

    def embed(self, texts, *, query=False):
        (self.query_calls if query else self.document_calls).append(list(texts))
        return np.asarray(
            [[float("needle" in text), float("other" in text), 0.1] for text in texts]
        )


@pytest.mark.parametrize("query,limit", [("needle", 6), ("!!!", 0), ("x" * 600, 99)])
def test_baseline_is_exact_existing_search(tmp_path, query, limit):
    directory = snapshot(tmp_path, [("One", "# One\nneedle"), ("Two", "# Two\nother")])
    original = Corpus(directory)
    experimental = ExperimentalCorpus(directory, mode="baseline")
    assert experimental.search(query, limit) == original.search(query, limit)


@pytest.mark.parametrize("mode", ["baseline", "contextual", "hybrid"])
def test_navigation_and_evidence_identity_are_unchanged(tmp_path, mode):
    directory = snapshot(
        tmp_path,
        [
            ("Source", "# Source\n[Target](page-1.md)\n## Detail\nneedle"),
            ("Target", "# Target\nother"),
        ],
    )
    original = Corpus(directory)
    experimental = ExperimentalCorpus(directory, mode=mode, embedder=FakeEmbedder())
    assert experimental.snapshot_id == original.snapshot_id
    for page_id in original.pages:
        assert experimental.outline(page_id) == original.outline(page_id)
        for passage in original.pages[page_id]:
            assert experimental.read(page_id, passage.section).evidence("S7") == passage.evidence(
                "S7"
            )
            assert experimental.outgoing_links(page_id, passage.section) == original.outgoing_links(
                page_id, passage.section
            )
    results = experimental.search("needle", 8)
    assert set(results) == {"query", "results", "note"}
    for hit in results["results"]:
        assert set(hit) == {"page_id", "section", "title", "heading", "url", "snippet"}
        assert hit["snippet"] == original.read(hit["page_id"], hit["section"]).text[:1100]


def test_context_is_source_prose_and_parent_headings_not_navigation(tmp_path):
    intro = "This introductory paragraph describes the document's actual purpose and scope."
    directory = snapshot(
        tmp_path,
        [
            (
                "Guide",
                "# Guide\n[Navigation](page-1.md)\n\n"
                + intro
                + "\n## Parent capability\nParent text\n### Child\nDetailed needle body",
            ),
            (
                "Index",
                "# Index\n> ## Documentation Index\n\n- [Link](page-0.md)\n"
                "\n```text\nThis code should not become the descriptive introductory paragraph.\n```\n"
                "## More\nThis is section prose, not the introductory paragraph.",
            ),
        ],
    )
    corpus = ExperimentalCorpus(directory, mode="contextual")
    contexts = source_contexts(corpus.passages)
    child = next(i for i, p in enumerate(corpus.passages) if p.heading == "Child")
    assert intro in contexts[child]
    assert "Parent capability" in contexts[child]
    assert "Navigation" not in contexts[child]
    assert not any("This code" in c or "This is section prose" in c for c in contexts)
    assert corpus.read("page-0", 2).text == "### Child\nDetailed needle body"


def test_intro_is_bounded_and_heading_stack_drops_previous_sibling(tmp_path):
    directory = snapshot(
        tmp_path,
        [
            (
                "Guide",
                "# Guide\n"
                + "actual prose " * 100
                + "\n## First\n### Nested\nBody\n## Second\nOther",
            )
        ],
    )
    corpus = Corpus(directory)
    contexts = source_contexts(corpus.passages)
    assert max(len(c.split("\n")[-1]) for c in contexts) <= 400
    assert "First" not in contexts[-1] and "Nested" not in contexts[-1]


def test_overlapping_windows_include_tail_and_do_not_exceed_token_limit():
    words = [f"word{i}" for i in range(51)]
    windows = token_windows(" ".join(words), WordTokenizer(), width=12, overlap=3)
    assert all(len(w.split()) <= 12 for w in windows)
    assert windows[0].split()[:3] == words[:3]
    assert windows[-1].split()[-1] == words[-1]
    assert set(" ".join(windows).split()) == set(words)
    assert windows[0].split()[-3:] == windows[1].split()[:3]


def test_fusion_fixed_equal_weight_ranks_and_snapshot_ties():
    assert reciprocal_rank_fusion([0, 1], [1, 0]) == [0, 1]
    assert reciprocal_rank_fusion([0, 1, 2], [2, 1, 3])[0] == 2
    assert 100 not in reciprocal_rank_fusion(list(range(101)), [])


@pytest.mark.parametrize("mode", ["contextual", "hybrid"])
def test_search_caps_pages_and_k_after_ranking(tmp_path, mode):
    documents = [
        (f"Page {i}", "# Header\nneedle\n## More\nneedle\n## Last\nneedle") for i in range(6)
    ]
    corpus = ExperimentalCorpus(snapshot(tmp_path, documents), mode=mode, embedder=FakeEmbedder())
    if mode == "contextual":
        corpus.contextual_index.get_scores = lambda words: np.full(
            len(corpus.passages), int(bool(words))
        )
    hits = corpus.search("needle", 99)["results"]
    assert len(hits) == 8
    assert max(Counter(h["page_id"] for h in hits).values()) == 2
    assert len(corpus.search("needle", 0)["results"]) == 1
    assert corpus.search("!!!")["results"] == []


def test_semantic_scores_use_best_window_including_tail(tmp_path):
    directory = snapshot(
        tmp_path, [("Long", "# Long\n" + "filler " * 90 + "needle"), ("Other", "# Other\nother")]
    )
    embedder = FakeEmbedder()
    corpus = ExperimentalCorpus(directory, mode="hybrid", embedder=embedder)
    corpus.contextual_index.get_scores = lambda _: np.zeros(len(corpus.passages))
    assert corpus.search("needle")["results"][0]["page_id"] == "page-0"
    assert len(embedder.document_calls) == 1  # Corpus windows encoded in one batched invocation.
    assert any("needle" in text for text in embedder.document_calls[0])


def test_cache_reuses_vectors_and_invalidates_model_or_snapshot(tmp_path):
    directory = snapshot(tmp_path / "docs", [("One", "# One\nneedle")])
    cache = tmp_path / "cache"
    first = ExperimentalCorpus(directory, mode="hybrid", embedder=FakeEmbedder(), cache_dir=cache)
    second_encoder = FakeEmbedder()
    second = ExperimentalCorpus(directory, mode="hybrid", embedder=second_encoder, cache_dir=cache)
    assert second.cache_hit and not second_encoder.document_calls
    assert np.array_equal(first.vectors, second.vectors)
    changed = ExperimentalCorpus(
        directory, mode="hybrid", embedder=FakeEmbedder("second"), cache_dir=cache
    )
    assert not changed.cache_hit and changed.cache_key != first.cache_key
    snapshot(directory, [("One", "# One\nchanged source")])
    changed = ExperimentalCorpus(directory, mode="hybrid", embedder=FakeEmbedder(), cache_dir=cache)
    assert not changed.cache_hit and changed.cache_key != first.cache_key


@pytest.mark.parametrize("fault", ["corrupt", "wrong_key", "wrong_dimension"])
def test_cache_fault_recomputes_instead_of_using_stale_vectors(tmp_path, fault):
    directory = snapshot(tmp_path / "docs", [("One", "# One\nneedle")])
    cache = tmp_path / "cache"
    first = ExperimentalCorpus(directory, mode="hybrid", embedder=FakeEmbedder(), cache_dir=cache)
    path = cache / f"{first.cache_key}.npz"
    if fault == "corrupt":
        path.write_bytes(b"not a vector cache")
    else:
        vectors = np.ones((len(first.vectors), 9), dtype=np.float32)
        np.savez(
            path,
            key="wrong" if fault == "wrong_key" else first.cache_key,
            vectors=vectors,
            sha256=hashlib.sha256(vectors.tobytes()).hexdigest(),
        )
    encoder = FakeEmbedder()
    rebuilt = ExperimentalCorpus(directory, mode="hybrid", embedder=encoder, cache_dir=cache)
    assert not rebuilt.cache_hit and len(encoder.document_calls) == 1


def test_query_character_truncation_is_shared_and_recorded(tmp_path):
    directory = snapshot(tmp_path, [("One", "# One\nneedle")])
    encoder = FakeEmbedder()
    corpus = ExperimentalCorpus(directory, mode="hybrid", embedder=encoder)
    query = "needle " * 100
    assert corpus.search(query)["query"] == query
    assert encoder.query_calls[-1] == [query[:500]]
    assert corpus.last_search_stats == {
        "query_chars": 700,
        "used_query_chars": 500,
        "query_truncated": True,
    }


def test_invalid_embedding_cannot_enter_index(tmp_path):
    directory = snapshot(tmp_path, [("One", "# One\nneedle")])
    encoder = FakeEmbedder()
    encoder.embed = lambda texts: np.full((len(texts), 3), np.nan)
    with pytest.raises(ValueError, match="nonfinite"):
        ExperimentalCorpus(directory, mode="hybrid", embedder=encoder)


def test_model_file_pins_reject_substituted_bytes_before_optional_imports(tmp_path):
    for name in backend["MODEL_FILES"]:
        (tmp_path / name).write_bytes(b"substituted artifact")
    with pytest.raises(ValueError, match="frozen SHA256 pins"):
        backend["PinnedFastEmbed"](tmp_path)
