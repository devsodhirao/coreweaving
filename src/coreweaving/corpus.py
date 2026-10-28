"""Deterministic section search over a hash-checked, local Weave documentation snapshot."""

import hashlib
import json
import posixpath
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from markdown_it import MarkdownIt
from rank_bm25 import BM25Okapi

from coreweaving.config import ROOT


def page_url_identity(url: str) -> tuple[str, str, int, str] | None:
    """Normalize document URL aliases for lookup, never for fetching."""
    if re.search(r"[\x00-\x20\x7f\\]", url) or re.search(r"%(?![0-9a-fA-F]{2})", url):
        return None
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        port = parts.port if parts.port is not None else (443 if parts.scheme == "https" else 80)
    except ValueError:
        return None
    path = posixpath.normpath(parts.path or "/").rstrip("/").removesuffix(".md")
    return parts.scheme, parts.hostname.lower(), port, path or "/"


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
    """Validate a frozen snapshot, then index its sections for local BM25 search."""

    def __init__(self, directory: Path = ROOT / "data/docs"):
        manifest = json.loads((directory / "manifest.json").read_text())
        # The reference page's source tag does not establish every guide's compatibility.
        self.docs_sdk_version = manifest.get("reference_sdk_version") or "unknown"
        self.pages: dict[str, list[Passage]] = {}
        self.passages: list[Passage] = []
        markdown_parser = MarkdownIt("commonmark", {"html": False})
        self._page_urls: dict[str, tuple[str, str]] = {}
        self._url_pages: dict[tuple, str] = {}
        self._passage_links: dict[str, list[list[str]]] = {}
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
            if page_id in self.pages:
                raise ValueError(f"Duplicate page_id in snapshot: {page_id}")
            self._page_urls[page_id] = (page["canonical_url"], page["url"])
            for url in self._page_urls[page_id]:
                identity = page_url_identity(url)
                if identity is None:
                    raise ValueError(f"Invalid document URL in snapshot: {page_id}")
                previous = self._url_pages.get(identity)
                if previous is not None and previous != page_id:
                    raise ValueError(f"Ambiguous document URL alias: {previous}, {page_id}")
                self._url_pages[identity] = page_id
            hashes.append(page["canonical_url"] + page["sha256"])
            markdown = content.decode("utf-8")
            line_offsets = [0]
            for line in markdown.splitlines(keepends=True):
                line_offsets.append(line_offsets[-1] + len(line))
            link_blocks = []
            # Parse the whole document so code fences, inline code and reference
            # definitions keep their meaning even across a 7,000-character split.
            for block in markdown_parser.parse(markdown):
                hrefs = [
                    token.attrGet("href")
                    for token in block.children or []
                    if token.type == "link_open" and token.attrGet("href")
                ]
                if hrefs and block.map:
                    start, end = block.map
                    link_blocks.append((line_offsets[start], line_offsets[end], hrefs))
            # Keep headings with their prose; hard-cap long sections for context budgets.
            sections = markdown_sections(markdown)
            chunks, bounds = [], []
            section_start = 0
            for section in sections:
                start = section_start
                section_start += len(section)
                if not section.strip() or section.startswith("> ## Documentation Index"):
                    continue
                heading = section.splitlines()[0].lstrip("# ")
                for offset in range(0, len(section), 7000):
                    body = section[offset : offset + 7000]
                    chunks.append((heading, body))
                    bounds.append((start + offset, start + offset + len(body)))
            page_context = chunks[0][1][:2000] if chunks else ""
            # Keep only complete Markdown blocks within the exposed excerpts;
            # a cutoff through a block must not invent navigable prose links.
            self._passage_links[page_id] = [
                [
                    href
                    for lower, upper in [
                        (start, end),
                        (bounds[0][0], bounds[0][0] + len(page_context)),
                    ]
                    for link_start, link_end, hrefs in link_blocks
                    if lower <= link_start and link_end <= upper
                    for href in hrefs
                ]
                for start, end in bounds
            ]
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
        """Return ranked navigation hints, with at most two hits per page."""
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
        """Return an exact indexed passage; never fetch a model-supplied URL."""
        if page_id not in self.pages:
            raise ValueError("Unknown page_id. Use an exact page_id from search_docs.")
        if section < 0 or section >= len(self.pages[page_id]):
            raise ValueError(f"section must be between 0 and {len(self.pages[page_id]) - 1}")
        return self.pages[page_id][section]

    def outline(self, page_id: str) -> list[dict]:
        """List section headings for navigation, without exposing unread bodies."""
        return [{"section": p.section, "heading": p.heading} for p in self.pages[page_id]]

    def outgoing_links(self, page_id: str, section: int = 0) -> list[dict]:
        """Up to eight linked snapshot pages; headings/IDs confer no read authority."""
        self.read(page_id, section)
        links, seen = [], {page_id}  # Same-page navigation already has an outline.
        for href in self._passage_links[page_id][section]:
            try:
                # urljoin otherwise repairs malformed absolute links such as
                # https:target into a seemingly valid relative destination.
                if urlsplit(href).scheme and page_url_identity(href) is None:
                    continue
            except ValueError:
                continue
            targets = set()
            for base in self._page_urls[page_id]:
                try:
                    identity = page_url_identity(urljoin(base, href))
                except ValueError:
                    continue
                target = self._url_pages.get(identity)
                if target is not None:
                    targets.add(target)
            # A redirected page can give relative links two meanings. Never
            # choose between different known targets by lookup order.
            if len(targets) != 1:
                continue
            target = targets.pop()
            if target in seen or not self.pages[target]:
                continue
            seen.add(target)
            links.append({"page_id": target, "title": self.pages[target][0].title})
            if len(links) == 8:
                return links
        return links
