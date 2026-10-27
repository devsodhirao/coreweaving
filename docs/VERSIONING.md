# Versioning the product, evidence, and memory

A version should answer two questions: **what produced this result, and what must we recheck when something changes?** Git history alone cannot identify a model response: the documentation, prompts, configuration and grading rules also matter.

## Keep a small number of useful identities

| Layer | Current record | Why it matters |
| --- | --- | --- |
| Runnable product | Full Git commit; package version in `pyproject.toml`; tracked `uv.lock`; digest-pinned sandbox image | Check out an implementation with its declared dependencies. A release tag names an accepted milestone. |
| Agent behavior | `source_sha256`, `prompt_sha256`, `config_sha256`, verification mode and cache setting | Attribute an answer to the actual Python/app bytes, prompt/tool definitions and configuration, including local edits. The short source hash is the Weave agent version: it identifies the code build, while configuration and mode distinguish behavior. |
| Model | Requested model name plus each returned model identifier, provider response ID and usage | Record what the provider reports. An alias is not proof that the provider's weights never change. |
| Documentation | Corpus `snapshot_id`, locked manifest, saved original passages and URLs | Explain what evidence was available then. Restoring the locked snapshot checks its contents; an ordinary docs refresh is a new input. |
| Evaluation | Git/source/snapshot identity, frozen expanded dataset and SHA, assertion IDs, rubric version, judge model, seed, trial identity and actual Weave evaluation ID | Keep cases, attempts and measurement rules attributable. Different grading rules cannot silently replace an earlier score. |
| Answer memory | Unique answer ID, original result, context/evidence/usage, separate dated review history | A later opinion or a new implementation must not rewrite the original answer. Older saved records can legitimately have unknown version fields. |

The prompt hash identifies the prompt/tool bundle, not every assembled provider request. Corpus identity covers canonical URLs and page bytes; the locked manifest also contains retrieval metadata, so the release records its separate hash.

The source hash currently covers `src/coreweaving/*.py` and `app.py`. It does **not** identify the entire environment, lockfile, sandbox image or raw documentation; those have separate records. Hashes identify bytes, not correctness. A timestamp is useful provenance, not a substitute for a content identity.

The manifest records `reference_sdk_version=0.53.1` from the Python reference page's source links. The installed SDK is `0.54.0`. These are separate trace attributes, and the sidebar shows the mismatch. This is the reference page's source tag, not a compatibility declaration for all 351 guides. Adding this metadata did not change the document bytes or corpus identity. API existence against the pinned runtime remains a separate future check.

## Documentation freshness and version support

**The assistant uses stored documentation. It tracks versions for provenance; it does not select or validate SDK releases.** The active corpus contains 351 Weave pages fetched October 24, 2026 at approximately 19:04 Pacific (October 25, 02:04 UTC), with snapshot identity `4db7c17b2869`. Fetch time is not the upstream publication date or a promise that the pages remain current.

| Capability | Current behavior and limit |
| --- | --- |
| Source identity | [Corpus](../src/coreweaving/corpus.py) validates page hashes; answers retain original passages and the snapshot ID. Hashes establish which bytes were used, not whether they are current or correct. |
| Freshness | No live retrieval, scheduled update, upstream change detector or snapshot-age warning. The library compares a saved answer with the **loaded snapshot**, not the live website. Citation URLs can change independently of saved evidence. |
| Release selection | One active corpus in the app. No SDK-version selector, release-specific search or migration comparison. The reference page's 0.53.1 label does not assign that version to all guides. |
| Compatibility | Runtime Weave is pinned to 0.54.0, but generated examples are not automatically checked for API existence, signatures or compatibility. The offline Python tool does not execute live SDK integrations. |
| Reproducibility | The bundled archive supports offline restoration of this snapshot. Identical inputs do not guarantee identical model responses or unchanged provider aliases. |

## Updating the corpus

This is a maintainer workflow, not an app feature.

1. Preserve the existing checkout and evidence. In a separate checkout, `uv run python scripts/fetch_docs.py --refresh --weave-only` downloads current pages and rewrites the manifest. Inspect the exit status, failures and content changes: a failed refresh can still leave a new, incomplete manifest.
2. Rebuild the bundled archive from the accepted pages and update the archive path/checksum in [fetch_docs.py](../scripts/fetch_docs.py). **Refresh does not do this automatically; no archive-building command is provided.** Validate a fresh offline restore before publishing. A refreshed manifest paired with the old bundle may fail locked restoration.
3. Restart the app or clear its resource cache, then start a new conversation. [The app caches its loaded corpus](../app.py); changing files on disk alone does not activate new evidence. Reevaluate the new snapshot, record its identities and preserve the earlier results. Old saved answers remain historical and require review before reuse.

## Changes should trigger proportionate evidence

- **Presentation-only:** open the artifact, inspect desktop and mobile, exercise the changed control, and check markup/links/browser errors. Reuse existing answer records; do not pay for a new evaluation merely to change a heading.
- **Python comments/docstrings:** the source hash still changes. Compare executable syntax and model-facing prompts/schemas, run local checks and refresh code excerpts. A Pydantic model docstring can change a generated tool description, so it must not be assumed behavior-neutral. Keep historical evaluations tied to their original hashes.
- **Prompt, permissions, tool behavior or memory policy:** change the relevant Given/When/Then contract, test the boundary, then run targeted real cases. Record a new behavior identity. An expanded capability needs an explicit permission decision; a new version number cannot grant authority.
- **Model, retrieval or documentation snapshot:** preserve the previous input, run the relevant regression and difficult cases, and compare quality, cost and latency. Existing answers remain historical; a freshness warning is a reason to review, not proof they are false.
- **Dataset or judge rule:** assign a new dataset identity or rubric version. Preserve old scores and disclose why the instrument changed. If rescoring stored answers, label it as a rescore with the original prediction identity; it is not a fresh agent run.
- **Stored-record format:** add an explicit schema version and migration before the first incompatible change. Back up the local database, retain original payloads and test old records. We have not needed an incompatible migration yet; SQLite currently has no migration framework.

## Releases and rollback

Use focused ordinary Git commits, followed by an annotated tag for a tested runnable milestone. The package declares `0.1.0`. The dated submission tag `submission-2026-10-26` identifies the submitted checkout and its recorded evidence; it is separate from a claim of production stability. Patch increments are compatible fixes; minor increments introduce capabilities or deliberate behavior changes. A future stable interface can justify `1.0.0`. This is our release convention, not a reliability score.

A release records its code commit, source and dependency identities, documentation snapshot, runtime settings, evaluation directories, known limitations and check results. The release tag points to the final commit containing that evidence. Do not move a published tag to disguise a fix; create a new version. Keep experiments in separately named result directories and never overwrite a finished run.

Roll back by checking out the prior release into a separate working directory and restoring its locked environment and docs. Keep current answer records and public traces intact. Compare record compatibility before opening a newer database with old code. A rollback changes the runnable product, not history, account permissions or billing.

## BDD evidence already present

- Given a recorded answer, when we review it or save it again, then its original result survives unchanged: `tests/test_library.py::test_repeat_save_is_idempotent_and_cannot_overwrite_review_or_evidence` and `test_explicit_reviews_keep_history_and_do_not_rewrite_source_check`.
- Given newer source material, when records are read, then earlier snapshot identity remains attached to the earlier answer: `test_snapshot_identity_and_original_answers_survive_newer_runs`.
- Given a modified locked corpus, when it loads, then the integrity check rejects it: `tests/test_corpus.py::test_modified_snapshot_is_rejected`.
- Given a new agent turn, when it completes, then its runtime identities appear in its result and conversation attributes: `tests/test_agent.py::test_result_and_conversation_record_runtime_identity`.
- Given source changes during an evaluation, when prediction continues, then the run detects the mismatch while preserving the completed turn: `tests/test_evaluate.py::test_source_change_preserves_already_produced_turn`.

## Honest limits

Two early local library records predate the new source/prompt/configuration identities and turn trace ID. They retain their original snapshot, model and usage; missing fields stay unknown. We do not backfill today's version into yesterday's answer.

The app compares saved-answer snapshot identity with the loaded corpus; it does not check live freshness or every behavior/dependency identity. Per-run dependency/environment hashes and an explicit stored-payload schema version are future hardening. The release record can capture the locked environment without pretending those fields already exist on every historical turn. Provider nondeterminism, mutable model aliases and asynchronous external services mean even an identified configuration is not a promise of identical text on replay.
