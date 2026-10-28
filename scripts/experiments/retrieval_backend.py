"""Local retrieval experiment; never changes evidence or the production search path.

Optional hybrid dependency: fastembed==0.9.1. Provision the pinned model separately;
this module only loads local files and does not download models or send telemetry.
"""

import hashlib
import importlib.metadata
import inspect
import json
import re
import tempfile
from pathlib import Path

import numpy as np
from markdown_it import MarkdownIt
from rank_bm25 import BM25Okapi

from coreweaving.config import ROOT
from coreweaving.corpus import Corpus, tokens

MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_REPOSITORY = "Qdrant/bge-small-en-v1.5-onnx-Q"
MODEL_REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"
MODEL_FILE_SHA256 = {
    "config.json": "13582bcf2effc85b7bf3d3f5532e686bc1c9ce86bb009d10f0ec33cbe92299dd",
    "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    "tokenizer_config.json": "0b29c7bfc889e53b36d9dd3e686dd4300f6525110eaa98c76a5dafceb2029f53",
    "special_tokens_map.json": "5d5b662e421ea9fac075174bb0688ee0d9431699900b90662acd44b2a350503a",
    "model_optimized.onnx": "51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431",
}
MODEL_FILES = tuple(MODEL_FILE_SHA256)
MODEL_PROVENANCE = {
    "weights": "SHA256 matched the official Hugging Face model file",
    "weights_source": "https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/blob/main/model_optimized.onnx",
    "download_mirror": "https://github.com/sudarsan2507-hue/yt-knowledge-assistant",
    "mirror_commit": "35acdc7bc5893f87330ab04300cbf58f263fb7a7",
    "mirror_claimed_source_revision": "52398278842ec682c6f32300af41344b1c0b0bb2",
    "configuration": (
        "Exact mirror-file SHA256 pins; JSON inspected. Association with expected HF revision "
        "is inferred from the mirror snapshot path and official README-only parent commit, "
        "not verified against official small-file hashes."
    ),
}
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
RRF_K = 60
CANDIDATE_LIMIT = 100


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_contexts(passages: list) -> list[str]:
    """Use an actual introductory paragraph and ancestor headings, never summaries.

    Link-heavy navigation, lists, quotes, code and HTML cannot become the intro.
    The selected paragraph must precede the first second-level section heading.
    """
    parser = MarkdownIt("commonmark", {"html": False})
    contexts = []
    for page_id in dict.fromkeys(p.page_id for p in passages):
        page = [p for p in passages if p.page_id == page_id]
        text = "".join(p.text for p in page)
        blocks = parser.parse(text)
        lines = text.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        headings, intro = [], ""
        for i, block in enumerate(blocks):
            if block.type == "heading_open":
                headings.append((offsets[block.map[0]], int(block.tag[1:]), blocks[i + 1].content))
            if block.type != "paragraph_open" or block.level != 0 or intro:
                continue
            if any(level >= 2 for _, level, _ in headings):
                continue
            inline = blocks[i + 1]
            children = inline.children or []
            prose = " ".join(inline.content.split())
            linked = sum(t.type == "link_open" for t in children)
            if (
                40 <= len(prose)
                and not linked
                and not any(t.type in {"html_inline", "image"} for t in children)
                and not re.search(
                    r"documentation index|table of contents|^navigation\b", prose, re.I
                )
            ):
                intro = prose[:400]
        start, stack = 0, []
        cursor = 0
        for passage in page:
            while cursor < len(headings) and headings[cursor][0] <= start:
                _, level, heading = headings[cursor]
                stack = [(depth, title) for depth, title in stack if depth < level]
                stack.append((level, heading))
                cursor += 1
            parents = [title for _, title in stack if title != passage.heading]
            contexts.append("\n".join([" > ".join(parents)[:300], intro]).strip())
            start += len(passage.text)
    return contexts


def token_windows(text: str, tokenizer, width: int = 480, overlap: int = 64) -> list[str]:
    """Cover all source tokens, including the tail, within the encoder token window."""
    if not 0 <= overlap < width:
        raise ValueError("overlap must be nonnegative and smaller than width")
    offsets = tokenizer.encode(text, add_special_tokens=False).offsets
    if not offsets:
        return [text]
    windows, start = [], 0
    while start < len(offsets):
        end = min(start + width, len(offsets))
        # Re-tokenizing a word-piece boundary can change the token count.
        while True:
            window = text[offsets[start][0] : offsets[end - 1][1]]
            if len(tokenizer.encode(window).ids) <= width + 2:
                break
            end -= 1
            if end <= start:
                raise ValueError("Cannot fit one source token in an embedding window")
        windows.append(window)
        if end == len(offsets):
            break
        start = max(start + 1, end - overlap)
    return windows


class PinnedFastEmbed:
    """CPU-only adapter for separately provisioned, hash-pinned BGE artifacts."""

    def __init__(self, model_dir: Path, batch_size: int = 32, threads: int = 2):
        model_dir = Path(model_dir)
        files = {
            name: hashlib.sha256((model_dir / name).read_bytes()).hexdigest()
            for name in MODEL_FILES
        }
        if files != MODEL_FILE_SHA256:
            raise ValueError("Local model artifacts do not match the frozen SHA256 pins")

        from fastembed import TextEmbedding
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.encoder = TextEmbedding(
            model_name=MODEL_NAME,
            specific_model_path=str(model_dir),
            local_files_only=True,
            providers=["CPUExecutionProvider"],
            threads=threads,
        )
        if self.encoder.model.tokenizer.truncation["max_length"] != 512:
            raise ValueError("Expected the pinned BGE 512-token encoder")
        self.dimension = 384
        self.batch_size = batch_size
        self.identity = {
            "model": MODEL_NAME,
            "repository": MODEL_REPOSITORY,
            "expected_hf_revision": MODEL_REVISION,
            "provenance": MODEL_PROVENANCE,
            "files_sha256": files,
            "fastembed": importlib.metadata.version("fastembed"),
            "onnxruntime": importlib.metadata.version("onnxruntime"),
            "tokenizers": importlib.metadata.version("tokenizers"),
            "window_tokens": 480,
            "overlap_tokens": 64,
            "model_max_tokens": 512,
            "query_prefix": QUERY_PREFIX,
            "query_char_limit": 500,
            "query_token_policy": "reject rather than silently truncate above512",
            "document_token_policy": "all tokens in overlapping windows; max section cosine",
            "batch_size": batch_size,
            "threads": threads,
            "provider": "CPUExecutionProvider",
        }

    def windows(self, text: str) -> list[str]:
        return token_windows(text, self.tokenizer)

    def embed(self, texts: list[str], *, query: bool = False):
        inputs = [QUERY_PREFIX + text if query else text for text in texts]
        if any(len(self.tokenizer.encode(text).ids) > 512 for text in inputs):
            raise ValueError("Embedding input exceeds512 tokens; no silent truncation allowed")
        return np.asarray(
            list(self.encoder.embed(inputs, batch_size=self.batch_size)), dtype=np.float32
        )


def normalized(vectors, rows: int, dimension: int):
    values = np.asarray(vectors, dtype=np.float32)
    if values.shape != (rows, dimension) or not np.isfinite(values).all():
        raise ValueError("Invalid embedding shape or nonfinite values")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if (norms <= 0).any():
        raise ValueError("Zero embedding vector")
    return values / norms


def reciprocal_rank_fusion(sparse: list[int], dense: list[int]) -> list[int]:
    scores = {}
    for ranking in (sparse[:CANDIDATE_LIMIT], dense[:CANDIDATE_LIMIT]):
        for rank, index in enumerate(ranking, 1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores, key=lambda index: (-scores[index], index))


class ExperimentalCorpus(Corpus):
    """Change navigation ranking only; the inherited evidence contract stays exact."""

    def __init__(
        self,
        directory: Path = ROOT / "data/docs",
        *,
        mode: str = "baseline",
        embedder=None,
        cache_dir: Path | None = None,
    ):
        if mode not in {"baseline", "contextual", "hybrid"}:
            raise ValueError("Unknown retrieval mode")
        super().__init__(directory)
        self.mode, self.embedder = mode, embedder
        self.last_search_stats = {}
        self.cache_hit = False
        self.identity = {
            "mode": mode,
            "snapshot_id": self.snapshot_id,
            "backend_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "corpus_sha256": hashlib.sha256(Path(inspect.getfile(Corpus)).read_bytes()).hexdigest(),
            "rank_bm25": importlib.metadata.version("rank-bm25"),
            "numpy": np.__version__,
        }
        if mode == "baseline":
            return
        contexts = source_contexts(self.passages)
        self.index_texts = [
            f"{p.title} {p.heading} {p.heading} {p.text}\n{context}"
            for p, context in zip(self.passages, contexts, strict=True)
        ]
        self.contextual_index = BM25Okapi([tokens(text) for text in self.index_texts])
        self.identity["index_sha256"] = digest(
            [
                [p.page_id, p.section, p.url, text]
                for p, text in zip(self.passages, self.index_texts, strict=True)
            ]
        )
        if mode != "hybrid":
            return
        if embedder is None:
            raise ValueError("Hybrid mode requires a separately provisioned local embedder")
        self.identity.update(
            {"embedding": embedder.identity, "rrf_k": RRF_K, "candidate_limit": CANDIDATE_LIMIT}
        )
        windows, owners = [], []
        for index, text in enumerate(self.index_texts):
            section_windows = embedder.windows(text)
            windows.extend(section_windows)
            owners.extend([index] * len(section_windows))
        self.window_owners = np.asarray(owners, dtype=np.int64)
        self.identity["windows_sha256"] = digest([windows, owners])
        self.cache_key = digest(self.identity)
        self.vectors = self._vectors(windows, cache_dir)

    def _vectors(self, windows: list[str], cache_dir: Path | None):
        cache_path = Path(cache_dir) / f"{self.cache_key}.npz" if cache_dir else None
        if cache_path and cache_path.exists():
            try:
                with np.load(cache_path, allow_pickle=False) as saved:
                    vectors = saved["vectors"]
                    if str(saved["key"]) != self.cache_key:
                        raise ValueError("Stale embedding cache")
                    if str(saved["sha256"]) != hashlib.sha256(vectors.tobytes()).hexdigest():
                        raise ValueError("Corrupt embedding cache")
                    normalized(vectors, len(windows), self.embedder.dimension)
                    if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5):
                        raise ValueError("Unnormalized embedding cache")
                self.cache_hit = True
                return vectors
            except (OSError, ValueError, KeyError):
                pass  # Rebuild from the pinned local model, never accept stale vectors.
        vectors = normalized(self.embedder.embed(windows), len(windows), self.embedder.dimension)
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=cache_path.parent, suffix=".npz", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                try:
                    np.savez_compressed(
                        temporary,
                        key=self.cache_key,
                        vectors=vectors,
                        sha256=hashlib.sha256(vectors.tobytes()).hexdigest(),
                    )
                    temporary.flush()
                    temporary_path.replace(cache_path)
                finally:
                    temporary_path.unlink(missing_ok=True)
        return vectors

    def search(self, query: str, limit: int = 6) -> dict:
        self.last_search_stats = {
            "query_chars": len(query),
            "used_query_chars": len(query[:500]),
            "query_truncated": len(query) > 500,
        }
        if self.mode == "baseline":
            return super().search(query, limit)
        scores = self.contextual_index.get_scores(tokens(query[:500]))
        sparse = sorted(
            (i for i, score in enumerate(scores) if score > 0), key=lambda i: (-scores[i], i)
        )
        ranked = sparse
        if self.mode == "hybrid" and tokens(query[:500]):
            vector = normalized(
                self.embedder.embed([query[:500]], query=True), 1, self.embedder.dimension
            )[0]
            section_scores = np.full(len(self.passages), -np.inf)
            np.maximum.at(section_scores, self.window_owners, self.vectors @ vector)
            dense = sorted(range(len(self.passages)), key=lambda i: (-section_scores[i], i))
            ranked = reciprocal_rank_fusion(sparse, dense)
        results, page_counts = [], {}
        for index in ranked:
            passage = self.passages[index]
            if len(results) >= min(max(limit, 1), 8):
                break
            if page_counts.get(passage.page_id, 0) >= 2:
                continue
            page_counts[passage.page_id] = page_counts.get(passage.page_id, 0) + 1
            results.append(
                {
                    "page_id": passage.page_id,
                    "section": passage.section,
                    "title": passage.title,
                    "heading": passage.heading,
                    "url": passage.url,
                    "snippet": passage.text[:1100],
                }
            )
        return {
            "query": query,
            "results": results,
            "note": "Read relevant sections with read_page before citing them.",
        }
