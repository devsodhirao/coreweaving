# Coreweaving reviewer handoff

The repository and recorded evidence should explain the work without the chat transcript. Start with `git status --short` and `git log -5 --oneline`.

<!-- HANDOFF_STATUS_START -->
**Current runtime `3a49a50`, source `b746d92df4ed`: 13/13 cases, 48/48 assertions, $2.85.** Rubric 2.3 changes two case 03 fairness rules; all questions/references and 46 assertions remain fixed (43/46 baseline → 46/46 final). Manual review flags a generous case 02 hierarchy grade and incomplete illustrative code; the recorded judge pass is preserved. [End-to-end review](../results/brief-e2e-v1/review.md) · [Code map](CODE_MAP.md)

245 tests and Ruff pass. Fresh setup restores 351 pages offline. The final browser replay passed 4/4 tasks and 12/12 checks, with real follow-up context and once-only delivery; median 41.1 seconds and 340–383words remain usability limits. The intermediate replay's invalid generated tool history and all earlier failures remain visible.

The verifier enforces citation integrity but has no demonstrated factual-accuracy advantage in the pilot. Corrected old/new calibration tied 6/6; seven final selected fixtures matched expectations. The old Signal produced 14 false positives among 15 selected turns; the revised policy passed six fixtures and correctly left four final UI answers untagged. These are scoped observations, not reliability estimates.

Compare this checkout with [public main](https://github.com/devsodhirao/coreweaving/commits/main/) for publication. The original submission tag is unchanged. Email submission and rehearsal remain owner actions; inspection requires no new paid runs.
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
| Verification | `support` checks cited claims; `support+coverage` adds requested obligations and relevant research/history. Material failures require repair. Support mode alone can make one extra strict check using the configured judge model of up to four supported facts on exhaustion, explicitly labeled partial. Empty/research-only recovery verdicts cannot release factual bullets. Experimental `off` is refused by the web app. |
| Tracing | Conversation → turn → tools/chats; verifier subagent contains its own chats. Actual evaluation Call IDs and source/prompt/configuration/snapshot identity propagate into agent spans. Backend readback proves the parent chain. |
| Evaluation | Frozen 13-case regression plus six-case capability suite; 70 assertions total. The judge is an ordinary traced Call. Quality is independent of verifier flags; exact reference overlap and page count are diagnostics. Unique trial/prediction artifacts prevent overwrites. |
| Cost | All-turn agent and separate judge usage, dated cache-aware estimates, conservative shared experiment reservations. Partial/ungraded work stays in cost totals. Unknown returned usage stops further requests. |
| UI | Pending question and elapsed stage stay visible; a citation picker opens beside each answer. Answer first; a separate Sources & analysis dialog holds evidence, checks, cost/cache, versions and the Weave link. Inspection does not call the agent. One worker per conversation persists before rendering, so library navigation cannot interrupt a running question. Process restart is not durable job recovery. |
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
- Weave 0.54's adapter passed net input into an inclusive OTel field, creating negative native cost estimates. The final provider boundary normalizes trace usage while preserving raw receipts; the earlier 13 live-check model spans reconciled to nonnegative native costs.
- Actual preset testing exposed a false abstention despite relevant reads. A later calibration change regressed the overview and passed a code example missing assistant history, so that prompt change was reverted. The earlier final targeted check retained assistant history, but its overview still omitted monitoring timing; the latest repair review supersedes its readiness status. Preserve these [case reviews](../results/preset-check-summary.json); a source-check pass does not mean the task was answered completely.
- Partial recovery releases a newly checked, explicitly narrowed answer, not selected fragments from an unchecked draft. Independent review caught an empty-claims waiver and reproduced its rejection after the fix. The [real recovery check](../results/recovery-check-v1/receipt.json) validates one narrowed answer; none of the four submission UI questions needed that recovery path.

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

Tests use fake model responses except real Docker probes. Paid pilot, regression and preset checks are complete; do not start more runs merely to inspect the repository. [Fresh offline setup](../results/brief-e2e-v1/fresh-setup-final.json) restores all 351 documents and imports the final code without credentials or model calls. No billing settings were changed. Review and interview rehearsal are next.

[GitHub](https://github.com/devsodhirao/coreweaving) and the [Weave project](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving) are public. Start the local app using the README; its default address is `http://127.0.0.1:8501`. Local SQLite, expanded documentation and `.env` stay outside Git. A licensed, hash-pinned archive of the 351 Weave pages is included for offline restoration. Review requires no credential display, billing change or recruiter email.

Return findings with severity, exact file/line, reproduction or trace evidence, and practical consequence. Distinguish implementation bugs, instrument defects, missing evidence and optional ideas.
