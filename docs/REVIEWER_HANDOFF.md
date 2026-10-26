# Coreweaving reviewer handoff

The repository and recorded evidence should explain the work without the chat transcript. Start with `git status --short` and `git log -5 --oneline`.

<!-- HANDOFF_STATUS_START -->
**Ready for owner review:** all 196 local tests and Ruff lint/format checks pass. Current code is commit `c9107dd`, source `8e41f1247e9b5cdcf22b395aefcb45ee34641d2d20b323edd0c26dabfc844f72`. Its comments/docstrings improve navigation; executable syntax, prompts, schemas, rubric and Signal definition match the prior `cebca8e` / `a4b6f4d3` build. [Readability check](../results/readability-review.json) · [Code map](CODE_MAP.md)

The preset investigation corrected citation parsing and evidence handoff, separated answer inspection, and added a bounded, strictly rechecked partial recovery. [Recorded browser checks](../results/preset-check-summary.json) cost $2.8676069 including one recovery replay. The final two questions both delivered useful answers, but met 5/6 manual checks: the overview omitted monitoring timing. Its tracing example is a condensed scaffold. The empty-verdict recovery guard and saved-answer selection fix followed those live checks. Both have local tests; final desktop/mobile inspection on `a4b6f4d3` confirms the selected answer and trace remain paired without model calls.

Historical full regression remains 11/13 on `179a052`; the 36-run pilot remains support 10/12, coverage 8/12, off 7/12. There is no full regression on final source. No further paid runs are planned. Latest commits and artifact changes remain local and unpublished.
<!-- HANDOFF_STATUS_END -->

## Objective and constraints

The CoreWeave DevRel assessment requires a tool-calling Weave documentation agent, multi-turn context, self-verification, new agent tracing, online Signals, and `weave.Evaluation` with at least ten varied questions and an LLM judge. Public source and Weave evidence are required; the owner must be able to run and explain the product in the interview. Email submission and interview rehearsal remain owner actions.

The owner also asked for a useful product and teaching experience, bounded permissions, deliberate memory, the existing BDD method, cost transparency and documented learning. Research routing, knowledge links, voice and adaptive presentation without claiming those proposed capabilities are shipped. Use standard Git, not `gh`.

## Read first

1. [README](../README.md): setup, architecture and measured results.
2. [Behavior contract](BEHAVIOR_CONTRACT.md): intent, Given/When/Then, actual tests and limits.
3. [Research artifact](../research.html): product/education/engineering decisions, interactive behavior examples and evidence.
4. [Evidence index](../results/README.md): exact runs, hashes and interpretation limits.
5. [Versioning contract](VERSIONING.md): release conventions, exact identity scope, old-record limits and rollback.
6. [AI build log](AI_BUILD_LOG.md): proposals, independent review findings, corrections and actual outcomes.

## What exists

| Area | Implementation and boundary |
| --- | --- |
| Agent | One direct Sonnet tool loop with search/read/offline Python/submit; step/tool/repair limits. Common planner across experiment modes. |
| Verification | `support` checks cited claims; `support+coverage` adds requested obligations and relevant research/history. Material failures require repair. Support mode alone can make one extra strict check of up to four supported facts on exhaustion, explicitly labeled partial. Empty/research-only recovery verdicts cannot release factual bullets. Experimental `off` is refused by the web app. |
| Tracing | Conversation → turn → tools/chats; verifier subagent contains its own chats. Actual evaluation Call IDs and source/prompt/configuration/snapshot identity propagate into agent spans. Backend readback proves the parent chain. |
| Evaluation | Frozen 13-case regression plus six-case capability suite; 70 assertions total. The judge is an ordinary traced Call. Quality is independent of verifier flags; exact reference overlap and page count are diagnostics. Unique trial/prediction artifacts prevent overwrites. |
| Cost | All-turn agent and separate judge usage, dated cache-aware estimates, conservative shared experiment reservations. Partial/ungraded work stays in cost totals. Unknown returned usage stops further requests. |
| UI | Answer first; a separate Sources & analysis dialog holds evidence, checks, cost/cache, versions and the Weave link. Inspection does not call the agent. One worker per conversation persists before rendering, so library navigation cannot interrupt a running question. Process restart is not durable job recovery. |
| Memory | Six dialogue exchanges in process plus original session source records. Source ledger has no total size cap. New conversation resets working memory; it does not delete the local library or public traces. |
| Library | SQLite answers start unreviewed; explicit assessments have separate history. Original evidence remains unchanged. Never retrieved as documentation authority or automatically promoted. |
| Signals | Active `needs-review` monitor through CoreWeave Serverless Inference, with historical observed feedback and agent-name filtering. Pilot agent turns can qualify; Signal spending is outside the Anthropic budget. |
| Proposed only | Specialist routing, knowledge-link expansion, voice, adaptive answer renderers, automatic library→dataset promotion and persistent inferred preferences. |

## Findings that must survive review

- The original 12/13 run already exposed a failure; it was incorrect to say the evaluation could show none. Its missing fallibility caution was subsequently identified as a normative engineering expectation, not an explicit statement established by its selected product passages. Preserve that record and limitation.
- Case assertions must allow valid alternatives. Capability case04's `weave.Evaluation` requirement is narrower than its question; documented `EvaluationLogger` can answer that portion. Independent omissions also caused the observed first-repeat failures. Preserve primary scores and explain the rubric issue rather than silently rescoring for a better headline.
- A correct source check can leave out information that was already read. A different failure can arise because the relevant section was never read. Coverage, retrieval and citation integrity are separate diagnoses.
- Self-generated coverage lists are diagnostic. Compare modes using the same independent judge and frozen cases. Repeats and assertions are not independent new tasks. A small selected pilot does not establish broad reliability or statistical superiority.
- Caching was added without changing effort. The synthetic cache probe establishes a warm hit; actual agent usage is measured separately. Do not promise the proposed 60–70% reduction from parameter presence alone.
- Partial-run review caught undercounted ungraded predictions and non-atomic receipt writes. Accounting now includes those attempts and reconciles returned budget usage against completed receipts.
- The known Weave call/end502 requires replaying the original completed parent record. Pending storage merges can expose both unfinished and completed physical versions in list queries. Direct latest-only reads and the evaluation-results API verify actual scores. Do not rerun paid answers or delete evidence to tidy the UI.
- Topic redirection is model guidance. Tool dispatch, rejected arguments and container controls enforce capabilities. Fake-model tests prove those boundaries, not universal semantic prompt-injection resistance.
- Credential masking precedes model requests, conversation names, spans and persistence. Synthetic canary absent in the real backend payload; this is not general PII detection. Public examples remain the right input for this public project.
- Weave 0.54's adapter passed net input into an inclusive OTel field, creating negative native cost estimates. The final provider boundary normalizes trace usage while preserving raw receipts; all 13 live-check model spans now reconcile to nonnegative native costs.
- Actual preset testing exposed a false abstention despite relevant reads. A later calibration change regressed the overview and passed a code example missing assistant history, so that prompt change was reverted. The final targeted check retains assistant history, but its overview still omits monitoring timing. Preserve these [case reviews](../results/preset-check-summary.json); a source-check pass does not mean the task was answered completely.
- Partial recovery releases a newly checked, explicitly narrowed answer, not selected fragments from an unchecked draft. Independent review caught an empty-claims waiver and reproduced its rejection after the fix. The [real recovery check](../results/recovery-check-v1/receipt.json) validates one narrowed answer; neither final UI question needed that recovery path.

## Inspect these paths

- [agent.py](../src/coreweaving/agent.py): release policy, repair feedback, evidence selection, session isolation and trace parentage.
- [llm.py](../src/coreweaving/llm.py): cache markers, returned provider usage and budget boundary; retries disabled for experiments.
- [evaluate.py](../src/coreweaving/evaluate.py): assertion IDs/types, independent scoring, all-turn evidence, actual Weave evaluation linkage, atomic artifacts and completion recovery.
- [compare.py](../src/coreweaving/compare.py): paired identities, case-grouped repeats, missing/error cells, per-arm and shared spending.
- [budget.py](../src/coreweaving/budget.py) / [metrics.py](../src/coreweaving/metrics.py): reservations versus returned usage versus unknown charges. Sum child charges once, not parent plus child.
- [app.py](../app.py) / [library.py](../src/coreweaving/library.py): no paid reruns, original-result preservation, review history and source freshness.

## Verification and access

```bash
uv run pytest -q
uv run ruff check src app.py tests
uv run ruff format --check src app.py tests
git diff --check
```

Tests use fake model responses except real Docker probes. Paid pilot, regression and preset checks are complete; do not start more runs merely to inspect the repository. [Fresh local setup](../results/final-setup-preset-fixes.json) restores all 351 documents and imports the final code without credentials or model calls. No billing settings were changed. Review and interview rehearsal are next.

[GitHub](https://github.com/devsodhirao/coreweaving) and the [Weave project](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving) are public. The [hosted planning artifact](https://coreweaving-field-plan.modest-cove-1723.chatgpt.site/research.html) remains owner-private. The app is at `http://127.0.0.1:8501`; the local artifact is at `http://127.0.0.1:8766/research.html`. Local SQLite, raw documentation and `.env` stay outside Git. Never print keys, expand sharing, alter billing or send the recruiter email during review.

Return findings with severity, exact file/line, reproduction or trace evidence, and practical consequence. Distinguish implementation bugs, instrument defects, missing evidence and optional ideas.
