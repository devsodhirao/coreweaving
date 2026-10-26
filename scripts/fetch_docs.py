"""Download official docs with source URLs, timestamps, hashes, and resumable caching.

Run with Python alone: python3 scripts/fetch_docs.py
Only the Weave collection is searched by the application. Supporting docs help
developers understand the implementation without widening the agent's scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "docs"
INDEXES = [
    "https://docs.coreweave.com/_llms/en/forge/weights-and-biases.txt",
    "https://docs.coreweave.com/_llms/en/forge/weights-and-biases/reference.txt",
]
SUPPORTING = {
    "anthropic": [
        "https://platform.claude.com/docs/en/get-started",
        "https://platform.claude.com/docs/en/api/messages/create",
        "https://platform.claude.com/docs/en/api/models/list",
        "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview",
        "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use",
        "https://platform.claude.com/docs/en/build-with-claude/structured-outputs",
        "https://platform.claude.com/docs/en/api/errors",
        "https://platform.claude.com/docs/en/about-claude/pricing",
    ],
    "streamlit": [
        "https://docs.streamlit.io/develop/api-reference/chat/st.chat_message",
        "https://docs.streamlit.io/develop/api-reference/chat/st.chat_input",
        "https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state",
        "https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps",
    ],
    "forge": [
        "https://docs.coreweave.com/products/inference/serverless.md",
        "https://docs.coreweave.com/products/wandb/platform/hosting/iam/api-keys.md",
        "https://docs.coreweave.com/products/wandb/platform/hosting/privacy-settings.md",
    ],
}


def get(url: str) -> tuple[bytes, str, str]:
    request = Request(url, headers={"User-Agent": "coreweaving-docs-snapshot/0.1"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read(), response.geturl(), response.headers.get_content_type()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def reference_sdk_metadata(pages: list[dict], directory: Path = DESTINATION) -> dict:
    """Source-tag version of the reference page, not a compatibility claim for all guides."""
    page = next((p for p in pages if p["url"].endswith("/weave/reference/python-sdk.md")), None)
    versions = set()
    if page:
        versions = set(
            re.findall(
                r"github\.com/wandb/weave/blob/v([^/\s)]+)/", (directory / page["file"]).read_text()
            )
        )
    return {
        "reference_sdk_version": next(iter(versions)) if len(versions) == 1 else "unknown",
        "reference_sdk_page": page["canonical_url"] if page else "unknown",
    }


def snapshot(refresh: bool = False, locked: bool = False, weave_only: bool = False) -> dict:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest_path = DESTINATION / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    existing = {item["url"]: item for item in previous.get("pages", [])}
    requested: dict[str, dict] = {}
    indexes = []
    for index_url in [] if locked else INDEXES:
        content, final_url, _ = get(index_url)
        index_path = DESTINATION / "indexes" / Path(urlparse(index_url).path).name
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_bytes(content)
        indexes.append(final_url)
        for title, url in re.findall(r"\[([^\]]+)\]\((https://[^)]+)\)", content.decode()):
            if "/weave" in urlparse(url).path and url.endswith(".md"):
                requested[url] = {"collection": "weave", "title": title, "url": url}
    for collection, urls in ({} if locked else SUPPORTING).items():
        for url in urls:
            requested[url] = {
                "collection": collection,
                "title": urlparse(url).path.rsplit("/", 1)[-1],
                "url": url,
            }
    if locked:
        if not existing:
            raise ValueError("--locked requires the committed manifest.json")
        requested = {
            url: {key: item[key] for key in ("collection", "title", "url")}
            for url, item in existing.items()
        }
        indexes = previous["indexes"]
    if weave_only:
        requested = {url: item for url, item in requested.items() if item["collection"] == "weave"}
    pages, failures = [], []

    def download(item: dict) -> dict:
        url = item["url"]
        old = existing.get(url)
        if old and not refresh:
            path = DESTINATION / old["file"]
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == old["sha256"]:
                return old
        content, final_url, content_type = get(url)
        if url.endswith(".md") and (
            "html" in content_type or content.lstrip().lower().startswith(b"<!doctype html")
        ):
            raise ValueError("Expected Markdown but received HTML; refusing to index an error page")
        digest = hashlib.sha256(content).hexdigest()
        if locked and digest != old["sha256"]:
            raise ValueError(
                "Upstream content changed. Use --refresh deliberately and rerun evaluations."
            )
        path_slug = urlparse(url).path.strip("/").replace("/", "__")
        if not Path(path_slug).suffix:
            path_slug += ".html" if "html" in content_type else ".txt"
        relative = Path(item["collection"]) / path_slug
        target = DESTINATION / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if locked:
            return old
        return {
            **item,
            "canonical_url": final_url.removesuffix(".md"),
            "file": str(relative),
            "content_type": content_type,
            "bytes": len(content),
            "sha256": digest,
            "fetched_at": datetime.now(UTC).isoformat(),
        }

    print(f"Downloading/checking {len(requested)} official pages (8 workers).", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download, item): item for item in requested.values()}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                pages.append(future.result())
            except Exception as error:
                failures.append({"url": item["url"], "error": f"{type(error).__name__}: {error}"})
                print(f"FAILED {item['url']}: {type(error).__name__}", flush=True)
            if index % 25 == 0:
                print(f"{index}/{len(requested)} checked", flush=True)
    manifest = {
        **reference_sdk_metadata(pages),
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "indexes": indexes,
        "pages": sorted(pages, key=lambda item: item["url"]),
        "failures": failures,
    }
    if not locked:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"Saved {len(pages)} pages; {len(failures)} failures. Manifest: {manifest_path}", flush=True
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch a new snapshot of all pages.")
    parser.add_argument(
        "--locked", action="store_true", help="Restore the committed snapshot; reject changes."
    )
    parser.add_argument(
        "--weave-only", action="store_true", help="Only fetch the agent's Weave corpus."
    )
    options = parser.parse_args()
    if options.refresh and options.locked:
        parser.error("--refresh and --locked cannot be combined")
    result = snapshot(refresh=options.refresh, locked=options.locked, weave_only=options.weave_only)
    raise SystemExit(1 if result["failures"] else 0)
