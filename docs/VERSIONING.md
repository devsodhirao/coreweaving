# Versions and reproducibility

A result needs the identity of its code, source material, model configuration and grading rules. These identify what ran; they do not establish correctness or guarantee identical model output.

## What is recorded

| Identity | Record and scope |
| --- | --- |
| Code | Full Git commit; `source_sha256` covers `src/coreweaving/*.py` and `app.py`. Its first 12 characters identify the Weave agent version. Documentation-only edits do not change this hash. |
| Behavior | Prompt/tool bundle hash, configuration hash, verification mode and cache setting. The prompt hash does not describe every assembled request. |
| Model | Requested and returned identifiers, provider response ID and usage. Mutable aliases may change behind the same name. |
| Corpus | Snapshot ID, locked manifest/page hashes, original passages and URLs. Snapshot identity covers canonical URLs and bytes; the manifest separately records retrieval metadata. |
| Evaluation | Source/snapshot, frozen dataset and assertions, rubric version, judge, trial/prediction IDs and Weave evaluation ID. |
| Saved answers | Original result and evidence plus separate review history. Missing fields in older records remain unknown. |

The locked environment and digest-pinned sandbox image are separate from the source hash. The package version is `0.1.0`; it is not a reliability rating. [Evidence by version](../results/README.md)

## Documentation freshness and version support

The assistant uses **one stored snapshot**, containing 351 pages fetched October 24, 2026 (Pacific), identity `4db7c17b2869`. The bundled archive restores those bytes offline. Fetch time is not an upstream publication date.

Reference-page source links identify SDK **0.53.1**; runtime Weave is pinned to **0.54.0**. The sidebar and trace attributes record this mismatch. It does not establish a release version for every guide or validate generated examples against the installed SDK.

There is no live retrieval, scheduled refresh, release selector, API-existence check or compatibility guarantee. Saved-answer freshness compares against the loaded snapshot, not the live site. Citation URLs can change while retained evidence stays intact. [Corpus implementation](../src/coreweaving/corpus.py)

## Updating the corpus

This is a manual maintainer operation:

1. Preserve the old checkout/results. In a separate checkout, `uv run python scripts/fetch_docs.py --refresh --weave-only` downloads current pages and rewrites the manifest. Inspect failures and changed content; a failed refresh can leave an incomplete manifest.
2. Rebuild the bundled archive from accepted pages and update its path/checksum in [fetch_docs.py](../scripts/fetch_docs.py). Refresh does **not** build that archive automatically. Confirm a fresh offline restore before publishing.
3. Restart the app or clear its resource cache, then start a new conversation. Review changed references and evaluate the new snapshot; changing files alone does not replace the cached corpus. Preserve historical answers and scores.

## What a change requires

| Change | Required evidence |
| --- | --- |
| Public documentation | Check factual claims and local links; inspect any changed rendered artifact. Retain the existing runtime measurement. |
| Python, prompts, tools or memory | Check the new source identity and relevant tests; run targeted behavioral checks. Pydantic docstrings can affect tool schemas, so a wording change may change behavior. |
| Model, retrieval or snapshot | Freeze the other conditions; compare quality, refusals, cost and latency on appropriate tasks. Do not reuse historical controls as if only one variable changed. |
| Dataset or judge | Version the instrument and preserve earlier scores. Explain the correction; a rescore is not a fresh agent run. |
| Persistent record format | Preserve original payloads and test compatibility before migration. SQLite currently has no migration framework. |

The original `submission-2026-10-26` tag remains at checkout `5225ea3` (runtime `755036e`). Later results describe runtime `3a49a50`; these are distinct milestones. Do not move a published tag or overwrite a completed run to present a new result as the old one.

To roll back, use a separate checkout with its locked environment and corpus. Preserve current saved answers/traces and check database compatibility before using an older runtime. A code rollback does not change account permissions or billing.

## Tested boundaries and remaining gaps

[Corpus tests](../tests/test_corpus.py) reject modified snapshot bytes. [Agent tests](../tests/test_agent.py) check runtime identities; [evaluation tests](../tests/test_evaluate.py) preserve a completed turn when source changes mid-run. [Library tests](../tests/test_library.py) preserve original answers and review history.

Per-turn environment hashes and explicit stored-payload schema versions remain future work. Provider nondeterminism and external-service changes prevent byte-identical answers from being promised even when the recorded inputs match.
