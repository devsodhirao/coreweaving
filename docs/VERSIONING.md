# Versions and reproducibility

Every result belongs to its code, corpus, configuration and grading instrument. Those identities explain what ran; they do not promise identical model output or correctness.

**Current runtime:** `522c320`, verification contract 6. [Progress](PROGRESS.md) tracks completed work and remaining gaps; the [validation packet](../results/essence-v2/README.md) separates original runs, the operational retry and independent review. Source is `bd74bb83b9fd34273acb50edcec66ea4ba0a5cf865ae867b2fc04cd84229a839`; the prior 13/13 on `dfdb6bd` remains historical.

## Recorded identities

| Identity | Record and scope |
| --- | --- |
| Code | Git commit plus `source_sha256` covering `src/coreweaving/*.py` and `app.py`; its first 12 characters identify the Weave agent version. Docs-only edits do not change this hash. |
| Behavior | Prompt/tool bundle hash, configuration hash, verification mode, caching and citation/verification versions. The prompt hash is not a hash of every assembled request. |
| Models | Configured roles, requested/returned identifiers, response IDs, usage and per-call effort. Mutable aliases can change behind the same name. |
| Corpus | Snapshot ID, manifest/page hashes, retained passages and canonical URLs. Fetch time is not publication time. |
| Evaluation | Frozen questions/assertions/references, rubric, settings, trial/prediction IDs and Weave evaluation ID. |
| Result | Original answer, sources, checks, usage and trace identifiers. Missing historical fields remain unknown. |

The lockfile and digest-pinned sandbox image are separate environment controls. Package version `0.1.0` is not a reliability rating. [`source_fingerprint`](../src/coreweaving/config.py) defines the code hash; [results](../results/README.md) preserve measurements by version.

## Contract history

| Contract | Meaning |
| --- | --- |
| Citation 3 — current | CommonMark-aware markers, including groups, must match declared read evidence. This establishes identity, not support. |
| Verification 1 — historical | Source-support checking and an optional source-derived coverage experiment. |
| Verification 2–3 — historical | Fixed question outcomes and verifier research, then workflow facets and evidence anchors. |
| Verification 4 — historical | Narrowed workflow expansion and added Python syntax checking; retained terminal rechecks and partial recovery. |
| Verification 5 — historical | One auditor checks the original question and read evidence; the writer owns research/repair. Separate planning, facets and terminal recovery were removed, but supported-claim inventories and quote gates remained. |
| Verification 6 — current | Same source/task responsibilities, with only `passed`, blocking `issues` and `missing_parts` returned by the model. Removes positive-claim quotation gates; retains citations, Python syntax, bounded repair and ordinary verification of partial answers. |

Citation and verification versions are independent. Retaining a contract number does not make two sources equivalent. Current modes are `support` and experimental `off`; `support+coverage` belongs to historical experiments.

`AGENT_MODEL` selects the writer/researcher, `VERIFIER_MODEL` the auditor, and `JUDGE_MODEL` the offline evaluator only. Agent calls request medium effort; offline grading retains provider-default effort. The pre-change paired diagnostic is inconclusive; earlier probes are not a general ranking. Changing the report schema creates a new measured source even when intended audit responsibilities stay the same. Record actual settings: `.env` can override defaults.

## Documentation freshness

The assistant uses **one stored snapshot** of 351 pages fetched October 24, 2026 (Pacific), identity `4db7c17b2869`. The bundled licensed archive restores those bytes offline. Citation URLs point to a live site that may change.

Reference links identify SDK **0.53.1**; installed Weave is pinned to **0.54.0**. The sidebar and turn attributes expose the mismatch. This does not date every guide or validate generated SDK examples.

There is no live retrieval, scheduled refresh, release selector or automatic API-compatibility check. Version identification exists; answering across selectable documentation releases does not.

## Updating safely

1. Preserve results and use a separate checkout. `uv run python scripts/fetch_docs.py --refresh --weave-only` downloads pages and rewrites the manifest. Inspect errors; failed refresh can leave it incomplete.
2. Rebuild the archive from accepted pages and update its path/checksum in [fetch_docs.py](../scripts/fetch_docs.py). Refresh does not build the archive automatically. Verify a fresh offline restore.
3. Restart the app or clear its resource cache, then start a new conversation. Review changed references and evaluate the new snapshot. Preserve old scores/evidence.

| Change | Verification needed |
| --- | --- |
| Public docs | Check claims/local links and changed rendered artifacts. Existing runtime scores retain their identity. |
| Source, prompt, tools or memory | New source identity, relevant behavior tests and live checks. Schema/docstring edits can alter requests. |
| Model, retrieval or corpus | Freeze other conditions and compare usefulness, refusals, cost and latency. Historical runs are not matched controls. |
| Dataset or judge | Version the instrument and explain changes. Rescoring is not a fresh agent run. |

Preserve published tags, including `submission-2026-10-26`, and completed result folders. Roll back in a separate checkout with locked dependencies and corpus; code rollback does not undo remote records or account settings.

[Corpus tests](../tests/test_corpus.py) reject changed bytes. [Agent tests](../tests/test_agent.py) check runtime identity/boundaries; [evaluation tests](../tests/test_evaluate.py) preserve incomplete work. The [auditor controls](../results/essence-v1/auditor-controls.json) freeze candidates, expected labels and exact corpus evidence independently of live results. Provider nondeterminism, platform differences and external-service changes remain reproducibility limits.
