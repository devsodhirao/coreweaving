"""Deterministic section search over a hash-checked, local Weave documentation snapshot."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from coreweaving.config import ROOT


def tokens(text: str) -> list[str]:
    # Keep API identifiers and also index their constituent words.
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return words + [part for word in words if "_" in word for part in word.split("_")]


def markdown_sections(text: str) -> list[str]:
    """A Python comment inside a fenced example is not a Markdown heading."""
    sections, current = [], []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token[0]
            elif token[0] == fence:
                fence = None
        if fence is None and re.match(r"^#{1,4} ", line) and current:
            sections.append("".join(current))
            current = []
        current.append(line)
    if current:
        sections.append("".join(current))
    return sections


@dataclass(frozen=True)
class Passage:
    page_id: str
    section: int
    title: str
    heading: str
    url: str
    page_sha256: str
    text: str
    page_context: str = ""

    def evidence(self, source_id: str) -> dict:
        return {"source_id": source_id, **asdict(self)}


class Corpus:
    def __init__(self, directory: Path = ROOT / "data/docs"):
        manifest = json.loads((directory / "manifest.json").read_text())
        self.pages: dict[str, list[Passage]] = {}
        self.passages: list[Passage] = []
        hashes = []
        for page in manifest["pages"]:
            if page["collection"] != "weave":
                continue
            content = (directory / page["file"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != page["sha256"]:
                raise ValueError(f"Snapshot hash mismatch: {page['file']}. Re-fetch the docs.")
            if content.lstrip().lower().startswith(b"<!doctype html"):
                raise ValueError(f"HTML in Markdown corpus: {page['file']}")
            # Use the indexed URL for identity: some canonical URLs redirect to
            # support outside /weave/. They must not collide with the landing page.
            page_id = page["url"].split("/weave", 1)[-1].removesuffix(".md").strip("/") or "index"
            hashes.append(page["canonical_url"] + page["sha256"])
            # Keep headings with their prose; hard-cap long sections for context budgets.
            sections = markdown_sections(content.decode("utf-8"))
            chunks = []
            for section in sections:
                if not section.strip() or section.startswith("> ## Documentation Index"):
                    continue
                heading = section.splitlines()[0].lstrip("# ")
                for offset in range(0, len(section), 7000):
                    chunks.append((heading, section[offset : offset + 7000]))
            page_context = chunks[0][1][:2000] if chunks else ""
            entries = [
                Passage(
                    page_id,
                    i,
                    page["title"],
                    heading,
                    page["canonical_url"],
                    page["sha256"],
                    body,
                    page_context,
                )
                for i, (heading, body) in enumerate(chunks)
            ]
            self.pages[page_id] = entries
            self.passages.extend(entries)
        if not self.passages:
            raise ValueError("No Weave pages found. Run scripts/fetch_docs.py.")
        self.snapshot_id = hashlib.sha256("\n".join(sorted(hashes)).encode()).hexdigest()
        self.index = BM25Okapi(
            [tokens(f"{p.title} {p.heading} {p.heading} {p.text}") for p in self.passages]
        )

    def search(self, query: str, limit: int = 6) -> dict:
        scores = self.index.get_scores(tokens(query[:500]))
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        results, page_counts = [], {}
        for index in ranked:
            passage = self.passages[index]
            if scores[index] <= 0 or len(results) >= min(max(limit, 1), 8):
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

    def read(self, page_id: str, section: int = 0) -> Passage:
        if page_id not in self.pages:
            raise ValueError("Unknown page_id. Use an exact page_id from search_docs.")
        if section < 0 or section >= len(self.pages[page_id]):
            raise ValueError(f"section must be between 0 and {len(self.pages[page_id]) - 1}")
        return self.pages[page_id][section]

    def outline(self, page_id: str) -> list[dict]:
        return [{"section": p.section, "heading": p.heading} for p in self.pages[page_id]]
