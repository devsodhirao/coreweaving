# Versions and reproducibility

A result needs the identity of its code, source material, model configuration and grading rules. These identify what ran; they do not establish correctness or guarantee identical model output.

**Current runtime:** commit `dfdb6bdfff88710d1b075c9839d38917c3a38fd1`; source SHA256 `2b4c8d1b6bbf70396fb63a68dcf55361e40bb6fd735fa292c8f803ae8d46c079`. Measurement checkout `6b05cf9` freezes the [final protocol](../results/product-final-v1/protocol.md). Its unchanged regression scored 13/13 cases and 48/48 assertions, with backend delivery verified. The seven-turn UI replay scored 17/18 outcomes and 5/6 tasks; a separate preset fulfilled its literal request. Backend readback reconciles all eight UI turns and 58 model spans in the [final packet](../results/product-final-v1/README.md). [V1](../results/product-repair-v1/README.md), source `55c77715…`, remains 12/13 cases and 46/48 assertions, with a partial preset answer after 66.6 seconds. [V2](../results/product-repair-v2/summary.json), source `5ed0e00…`, retains 16/18 UI outcomes, 4/6 passing tasks and a separately successful preset. Never relabel historical runs.

## What is recorded

| Identity | Record and scope |
| --- | --- |
| Code | Full Git commit; `source_sha256` covers `src/coreweaving/*.py` and `app.py`. Its first 12 characters identify the Weave agent version. Documentation-only edits do not change this hash. |
| Behavior | Prompt/tool bundle hash, configuration hash, verification mode, cache setting, `citation_contract_version` and `verification_contract_version`. The prompt hash does not describe every assembled request. |
| Model | Configured planner, verifier and judge roles; requested/returned identifiers, provider response ID, usage and per-call effort (`medium` or `provider_default` for current paths). Mutable aliases may change behind the same name. |
| Corpus | Snapshot ID, locked manifest/page hashes, original passages and URLs. Snapshot identity covers canonical URLs and bytes; the manifest separately records retrieval metadata. |
| Evaluation | Source/snapshot, frozen dataset and assertions, rubric version, judge, trial/prediction IDs and Weave evaluation ID. |
| Saved answers | Original result and evidence plus separate review history. Missing fields in older records remain unknown. |

The locked environment and digest-pinned sandbox image are separate from the source hash. The package version is `0.1.0`; it is not a reliability rating. [Evidence by version](../results/README.md)

## Two independent contract versions

**Citation contract version 3** parses CommonMark citations, including grouped IDs, using the UI's text normalization. It checks syntax and correspondence with read evidence, not semantic support.

**Verification version 2** introduced question-derived outcomes, applicability checks and typed repair research. **Version 3** added input, execution-trigger and output facets for selected workflows, with answer quotes and read-evidence anchors. **Version 4** instructs the planner to use ordinary outcomes for role/relationship overviews and reserve full facets for explicit requests for all three; it also rejects syntactically invalid recognized Python fences before model auditing. Exact quotes and IDs establish provenance, not semantic completeness. Task selection and entailment remain model judgments; parsing is not SDK validation. Partial recovery needs a fresh check and retains unresolved outcomes.

The source-support pilot and optional source-derived coverage experiment predate task checks, despite reusing mode names. Their results do not validate the current contract. Delivery-schema and output-budget changes also need distinct source/request identities even when a contract number is unchanged.

V1 changed credential handling, literal-reference telemetry encoding and agent effort as a bundle. V2 separated ordinary Opus verification through `VERIFIER_MODEL` from Sonnet planning through `AGENT_MODEL`. The final configuration defaults both, plus `JUDGE_MODEL`, to Opus 5.5 after [selected full-turn writer probes](../results/product-writer-probe-v1/review.json). Planning and verification use medium effort; offline grading retains provider-default effort and rubric 2.3. Contract 4 remains unchanged. Both model changes need distinct configuration/source identities and measured results; selected probes are not general accuracy estimates.

V2 also preserves reference-bearing SDK dataset containers in legacy telemetry; the final runtime retains that implementation. Inline Agent JSON protects literal URI-like text on a copy. The [no-model-call fixture](../results/product-index-repair-v2/interpretation.json), recorded on source `5ed0e00…`, verifies an indexed row, completed parent and direct scorer output; its scorer-ID index entry remains missing. This does not establish full-run delivery or repair v1's zero-row index snapshot.

The frozen repair requires and validates known live verdict fields while retaining historical-reader defaults. Unknown root, claim and outcome annotations are discarded, not stored or executed; typed research requests remain strict. Ordinary audits keep a 4,000-token cap; workflow audits use `min(9000, 4000 + 300 × facet_count)`, including provider thinking. Missing, invalid or truncated required data still fails closed. The [repair review](../results/task-completion-repair-v1/review.md) records delivery failures, subsequent passes and remaining semantic errors.

The later scheduling repair counts research dispatches separately from submissions. Planning calls and revisions remain bounded; the last planning call permits submission only. One existing terminal judge call may strictly recheck a complete draft after an auditor-record failure instead of reducing it to partial facts. Application-owned eligibility is excluded from the model schema; a failed full recheck gets no second fallback. These are source-versioned runtime changes, not rubric changes.

The planner delivery repair permits one fresh attempt after a truncated response, using the next existing planning slot with a 4,800-token allowance. Normal planner requests remain at 2,400. It discards the truncated response, preserves the frozen task and normal verification, and stops on repeated or final-slot truncation. The higher allowance is not an increase to the ten-call turn budget.

## Documentation freshness and version support

The assistant uses **one stored snapshot**: 351 pages fetched October 24, 2026 (Pacific), identity `4db7c17b2869`. The bundled archive restores those bytes offline. Fetch time is not publication time.

Reference-page links identify SDK **0.53.1**; runtime Weave is pinned to **0.54.0**. The sidebar and traces record this mismatch. It neither dates every guide nor validates generated examples against the installed SDK.

There is no live retrieval, scheduled refresh, release selector or compatibility guarantee. Saved-answer freshness compares snapshots, not the live site. Citation URLs can change while retained evidence stays intact. [Corpus implementation](../src/coreweaving/corpus.py)

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

The original `submission-2026-10-26` tag remains at checkout `5225ea3` (runtime `755036e`). October 27 describes `3a49a50`; the [October 28 review](../results/thorough-pass-2026-10-28/review.md) distinguishes `6761be2` and `ab9a92a`. Later task-contract probes are separate development evidence in the [evidence index](../results/README.md). Preserve published tags and completed runs.

Roll back in a separate checkout with its locked environment and corpus. Preserve saved answers/traces and check database compatibility. Code rollback does not change account permissions or billing.

## Tested boundaries and remaining gaps

[Corpus tests](../tests/test_corpus.py) reject modified snapshot bytes. [Agent tests](../tests/test_agent.py) check runtime identities; [evaluation tests](../tests/test_evaluate.py) preserve a completed turn when source changes mid-run. [Library tests](../tests/test_library.py) preserve original answers and review history.

The October 28 repairs retain rubric 2.3 and its existing questions/assertions. Evaluation now propagates `JUDGE_MODEL` into the recovery verifier and reports operational errors from every turn, including earlier turns before a successful follow-up. Neither correction rescales historical scores or reruns saved predictions.

Per-turn environment hashes and explicit stored-payload schema versions remain future work. Provider nondeterminism and external-service changes prevent byte-identical answers from being promised even when the recorded inputs match.
