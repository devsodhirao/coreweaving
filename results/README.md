# Evidence index

Start with the [decision guide](../docs/DECISIONS.md) for engineering judgment and use the versioned runs below for measurements. Recorded answers, failed attempts and labeled fixtures remain unchanged.

[Reviewer-gap work](reviewer-gaps-v1/README.md) confirms that the current runtime matches its existing regression. [Judge calibration](judge-calibration-v1/README.md) has 30 saved answers queued for owner labeling; no human agreement or new model measurement is claimed.

## Current full regression: `a07e5da` / source `b312a2c9a081`

The [presentation regression](presentation-regression-retry-v1/README.md) completed all 13 cases: **12/13 judge-recorded passes, 47/48 assertions**, no missing grades. The failure is an uncited product menu in a clarification; the answer checker accepted it. Median engine time was 31.46 seconds across 15 turns; returned-usage estimate $5.2549. Readback matches 15 turn roots, 97 agent responses and 13 indexed evaluation rows with their judge receipts. The runtime remains unchanged for the demo.

The [first attempt](presentation-regression-v1/README.md) timed out in its first judge call and produced no valid grades. Preserve its $0.24075 known estimate, one unpriced request and incomplete Agent delivery. The complete retry uses the same code, data, seed and rubric. It does not erase that operational failure or establish independent grading, broader accuracy or auditor value.

## Later wording and decision review: source `b312a2c9a081`

The [two-turn live walkthrough](decision-walkthrough-v1/README.md) records the current overview preset and contextual follow-up, desktop/mobile screenshots, 430 local tests, and remote delivery of both turns and 20 provider responses. Cost was $1.0136. The overview required three audits and still used imprecise Signal-scoring language; both responses were long. These observations do not replace the earlier regression or establish clarification accuracy.

The separately authorized [paired hybrid experiment](retrieval-live-v3/README.md) completed 24 answers on six existing questions. Both methods had 12/12 judge-recorded task passes, 20 searches and 70 model requests. Time/cost were mixed; retain BM25 provisionally. Total estimated model use was $7.6281, including one invalid grade and its disclosed retry. All 24 turns, 140 agent responses and 25 judge responses reconcile remotely. These are targeted development results, separate from the original pilot and full regression.

## Earlier full regression: `522c320`

Start with the [current packet](essence-v2/README.md). Source `bd74bb83b9fd34273acb50edcec66ea4ba0a5cf865ae867b2fc04cd84229a839`, verification contract 6 and unchanged rubric 2.3. One bounded research/check loop replaces separate planning, workflow facets, terminal recovery and the SQLite library.

- [Regression completion](essence-v2/regression-completion.json): **13 distinct cases assessed; judge-recorded 12/13 and 47/48 assertions.** This keeps the original twelve quality outcomes and adds one explicitly named billing-failure retry, costing $0.36. [Retry delivery](essence-v2/regression-resumption-backend-readback.json) · [Reviewer disagreement on implicit hierarchy](essence-v2/regression-resumption-review.json)
- [Regression](essence-regression-v2/summary.json): **11/13 planned cases passed**; initialization omits authentication/agent export, and the last task was blocked by exhausted Anthropic credit. **44/48 assertions passed**, one failed and three ungraded. $4.32 returned-usage estimate plus one rejected request with no usage returned. [Answer review](essence-v2/regression-review.json) · [Provider-failure evidence](essence-v2/provider-failure-readback.json)
- [Four captured-answer controls](essence-v2/auditor-check/semantic-review.json): both positives accepted; neither targeted negative defect identified in the reasons. Label agreement was 3/4, not demonstrated semantic repair.
- [Funded browser replay](essence-v2/ui-after-funding/answer-review.json): **17/18 frozen criteria, 5/6 strict tasks; all six literal requests fulfilled** in AI-assisted source/code review. Seven-turn terminal-prose median **23.383 seconds**, range **18.242–66.504**. The overview omits the checklist’s completed-turn timing detail. One late code block makes its exact full-render time unmeasured; it was visibly delivered. [Observer repair controls](essence-v2/observer-v3-proof.json). The [preceding source’s replay](essence-v1/ui/answer-review.json) remains historical.
- [428 tests/Ruff](essence-v2/local-checks.json), [clean-clone offline setup](essence-v2/fresh-setup.json) and [current Signal configuration](essence-v2/signal-readback.json) verified. The current failed turn received an [attributed needs-review tag](essence-v2/signal-error-readback.json); earlier scoring history remains preserved.

The [first simplification](essence-v1/README.md), source `216497c3aa9e…`, retains 12/13 assessed cases after a separate stored-answer grade, its original incomplete Evaluation, and every browser failure. The twelve-attempt [writer diagnostic](essence-v1/writer-diagnostic/review.json) used the preceding contract-5 source: Sonnet fulfilled 2/6 planned tasks, Opus 5/6, with one Sonnet attempt budget-interrupted. It failed to establish the complete selection rule; it is not a ranking for the changed auditor.

## Historical baseline before simplification: `dfdb6bd`

Runtime `dfdb6bdfff88710d1b075c9839d38917c3a38fd1`, source `2b4c8d1b6bbf70396fb63a68dcf55361e40bb6fd735fa292c8f803ae8d46c079`; measurement checkout `6b05cf9cf67851e096b94ec6e9e844aeb2c45141`. Opus 5.5 plans, writes and verifies at medium effort; the offline Opus judge retains provider-default effort. Verification contract 4 and regression rubric 2.3 are unchanged.

**The regression completed: 13/13 cases, 48/48 assertions, $4.5700258 estimated agent + judge cost.** There are no failed judges or ungraded assertions. [Exact run](product-final-regression-v1/summary.json)

[Backend readback](product-final-v1/evaluation-backend-readback.json) verifies the completed parent, all 13 indexed rows and exact scores, 15 Agent roots and 88 model spans without replay. Optional scorer-ID index metadata is absent; direct scorer records match. [Independent review](product-final-v1/regression-review.json) inspected all 13 cases/15 turns, matched 53 cited passage references and parsed seven Python fences, without a demonstrated material defect. This is not general correctness or SDK execution evidence.

The [actual seven-turn UI replay](product-final-v1/answer-review.json) passed **17/18 outcomes and 5/6 tasks**, with all seven answers delivered complete. The overview omits the frozen completed-turn timing requirement despite answering the literal role-comparison question. Median visible wait was 52.241 s, maximum 92.446 s; 48 calls cost $2.032156 estimated. The separate preset fulfilled its literal request in 76.671 s visible / 74.83 s engine time, with 10 calls and $0.4577432 estimated cost; it does not change the benchmark score. [UI readback](product-final-v1/backend-readback.json) reconciles all eight roots and 58 model spans, totaling $2.4898992. [Preset visual checks](product-final-v1/preset-smoke/visual-review.json) cover desktop/mobile layouts and the analysis dialog. [Current Signal configuration](product-final-v1/signal-readback.json) and [preserved earlier scoring](product-final-v1/signal-history.json) remain distinct.

[Local checks](product-final-v1/local-checks.json) already pass on this source: 599 tests and Ruff, with 336 SDK warnings retained. [Fresh setup](product-final-v1/fresh-setup.json) verifies the locked install, 351 pages restored from an empty cache with socket connections blocked, matching source identity and no credentials or API calls. These do not establish answer quality.

## Historical product repairs and model-selection evidence

| Runtime / experiment | Result and boundary |
| --- | --- |
| [V1 repair: `81c49c0`](product-repair-v1/README.md), source `55c77715…` | Seven UI turns: 17/18 outcomes, 5/6 tasks, median visible wait 20.2 s and $0.6381 estimated. The password example remains valid Python; overview timing is omitted. |
| [V1 regression](product-repair-regression-v1/summary.json) / [independent review](product-repair-v1/regression-review.json) | 12/13 cases, 46/48 assertions, $2.3456. Case 02 loses the direct answer through incomplete premise research and strict auditing; the final answer remains explicitly partial. |
| [V1 remote records](product-repair-v1/evaluation-backend-readback.json) / [direct call check](product-repair-v1/evaluation-direct-call-readback-v2.json) | 15 Agent roots and 84 model spans verified. All 13 stored predictions/scores match directly, but zero indexed evaluation rows were returned. The later fix does not rewrite this snapshot. |
| [V1 separate preset](product-repair-v1/regression-and-preset-summary.json) | One button click and one saved answer, 66.568 s, partial. Passing interaction/source checks did not establish task completion. |
| [V2: `3b24cd2`](product-repair-v2/summary.json), source `5ed0e00…` / [answer review](product-repair-v2/answer-review.json) | Sonnet writer + Opus verifier: 16/18 outcomes, 4/6 passing tasks, median visible wait 33.24 s. The overview was partial and the tracing follow-up had a material code defect. A separate preset fulfilled its literal request in 44.911 s. |
| [Stored-draft verifier probe](product-verifier-probe-v1/summary.json) | Eight calls, $0.5298: Opus accepted two scoped positives, Sonnet neither; both rejected both false controls. Opus was slower per check. Selected candidates, not a general accuracy estimate. |
| [Full-turn writer probe](product-writer-probe-v1/review.json) | Two literal tasks passed with Opus writing in 68.94/35.39 s, $0.6679 combined. The overview still omitted the separate benchmark timing criterion. Motivates wider validation, not a model ranking or speed claim. |
| [Dataset-reference indexing fixture](product-index-repair-v2/interpretation.json) | Zero model calls: complete parent and one indexed row, with direct prediction/scorer verification. The scorer-ID index entry remains unavailable. Earlier failed fixture preserved. |
| Versioned setup and local checks | [V1: 593 tests](product-repair-v1/local-checks.json), [v1 fresh setup](product-repair-v1/fresh-setup.json); [v2 checks](product-repair-v2/local-checks.json), [v2 fresh setup](product-repair-v2/fresh-setup.json). These apply to their recorded versions. |
| [Signal configuration](product-repair-v1/signal-readback.json) | Existing monitor enabled and exact runtime-reason filter verified; earlier eligible/excluded scoring controls remain preserved. |

The [actual Claude baseline](claude-product-baseline-v1/README.md) uses regular Claude Opus 5.5 at Extra effort with its native web tools. Both products met 14/15 outcomes on five clean task pairs; the sixth had inherited Claude history. This is a product comparison with unequal model/effort/freshness, not a retrieval-isolation experiment. All original answers and deviations are preserved.

## Retrieval comparison: keep the current default

The [current-runtime offline follow-up](retrieval-followup-v2/README.md) addresses a gap in that decision: the original live tasks excluded the three queries where hybrid improved retrieval. On six fresh wordings of selected known tasks, BM25 at six/eight results and hybrid at six found **52.8% / 52.8% / 66.7%** of selected evidence. Hybrid improved two queries and tied four; all-fact coverage stayed 2/6. No paid calls or agent answers were generated. This supports a targeted live comparison, not an adoption or superiority claim.

The [prospective retrieval probe](retrieval-comparison-v1/README.md) compares BM25, source-context BM25 and local hybrid search on 18 frozen queries. Selected-nugget recall@6 was **57.0% / 57.0% / 64.4%**. Hybrid's 7.4-point gain missed the predeclared 10-point threshold; all-nugget coverage stayed 7/18. In six paired agent tasks, both arms passed 14/14 assertions; hybrid used 35 model calls versus 36, with median engine time 24.78 s versus 28.42 s. One trial per arm and uneven verifier decisions prevent a causal speed claim. Total agent + judge estimate: **$2.44**.

The retrieval experiment left app runtime `fe4b7b5` unchanged. [Original scores](retrieval-comparison-v1/live/summary.json), [recomputed totals](retrieval-comparison-v1/live-comparison.json) and [independent review](retrieval-comparison-v1/live-review.json) preserve shared code-redaction defects and a citation attribution the runtime verifier accepted and the evaluation judge noted without failing the case. [Backend readback](retrieval-comparison-v1/backend-readback.json) separates 12 local scored records from incomplete remote delivery and failed Weave aggregation; [diagnosis](retrieval-comparison-v1/export-diagnosis.json) reproduces literal-text/reference confusion without network calls. [513 tests and local checks](retrieval-comparison-v1/local-checks.json). This experiment does not replace the regression results below.

## Prior task-completion repair

[Task-completion repair](task-completion-repair-v1/review.md) separates source support, task completion, audit delivery and output delivery. The questions and rubric stayed fixed throughout this pass.

| Runtime | Measurement | Finding |
| --- | --- | --- |
| `2adf56b` | UI 5/6, 17/18; regression partly ungraded | Overview omitted Signal timing despite a completion label. Provider failure left six judges ungraded. |
| `2033cec` / `a8aafb6` | Focused workflow probes rejected their positive control | Required-field delivery and unused annotation handling failed; original payloads are preserved. |
| `5d719e3` | UI 5/6, 16/18; regression 12/13, 46/48 | Shared research/submission counting and an auditor-record failure obstructed valid revisions. |
| `f4c7618` | [UI 6/6, 18/18](task-completion-repair-v1/ui-final-f4/manual-review.json); [regression 12/13, 43/48](task-completion-regression-v3/summary.json) | Original overview completes; usage follow-up retrieves the needed evidence but hits the planner output cap. |
| `fe4b7b5` | [Regression 12/13, 47/48](task-completion-regression-v4/summary.json); [two-turn UI 5/5 assertions](task-completion-repair-v1/ui-followup-fe4/manual-review.json) | One real truncated response receives a bounded retry and normal verification. The remaining failed clarification adds unsourced alternatives; manual review also finds an overbroad span claim in passing case 02. |

**Historical measured runtime:** `fe4b7b5ea5fe1b661945a7129cc9d8a29f6565ba`, source `860e9ee6c1134ca44ed04ac9dd22103e2c8acfe5f64fe40a0969941034af53ff`. [Independent answer review](task-completion-repair-v1/regression-v4-independent-review.json), [accounting](task-completion-repair-v1/regression-v4-accounting.json): $3.32 across 116 agent/judge calls. [479 tests/Ruff](task-completion-repair-v1/local-checks-retry.json), [fresh offline setup](task-completion-repair-v1/fresh-setup-retry.json), [unchanged instrument](task-completion-repair-v1/instrument-retry.json).

**Remote delivery remains incomplete:** [readback](task-completion-repair-v1/backend-retry.json) verifies all 17 Agent turns and the matching evaluation parent summary, but only 2 of 13 evaluation rows. [Exact-ID checks](task-completion-repair-v1/backend-retry-missing-rows-diagnostic.json) found missing underlying calls in sampled rows; the [pre-flush receipt](task-completion-repair-v1/backend-retry-before-flush.json) is preserved. No cases were rerun or reconstructed to mask the gap. All 17 runtime completion labels were positive, so the Signal correctly selected zero turns while missing semantic defects independently identified in cases 06 and 02.

The preceding `f4c7618` source is `3c771f7a2456d2e66362d13a1006f059b30751bb45717ab28952e32d35665945`. [Backend readback](task-completion-repair-v1/backend-budget.json) verifies all 21 UI/regression turns and all 13 evaluation rows; the one eligible failed turn received a Signal tag and 20 healthy turns were excluded. [Accounting](task-completion-repair-v1/regression-v3-accounting.json): 114 calls, $3.20. Its setup, instrument and 473-test receipts remain alongside those later historical records.

[New skill validation](skill-validation-v1/validation.json) is an offline instruction test, not proof of an MCP connection. Original hashes and any path sanitization are recorded beside copied receipts.

## Earlier complete repair result

Runtime `ab9a92a`, source `49e53739d78f81fcc69ecb2b48676413c4e3bfa63adf31c133bbf937d8de76d4`: **12/13 cases, 48/48 assertions, $2.52**, with rubric 2.3 and its questions/assertions unchanged. Case 01 failed the separate uncertainty gate despite passing its assertion checklist. No failed judge or missing prediction was counted as a quality score. [Run](thorough-repair-regression-v1/summary.json) · [Weave evaluation](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving/weave/calls/01a181c5-0a29-7ced-82ac-2598e9053c21)

| Check | Evidence for `ab9a92a` |
| --- | --- |
| Actual app | [5/6 tasks, 17/18 checks](thorough-pass-2026-10-28/ui-final/manual-review.json), $0.90; overview still omits Signal completion timing. Baseline and intermediate replays remain in the [review](thorough-pass-2026-10-28/review.md). |
| Traces | [UI](thorough-pass-2026-10-28/backend-ui.json) and [all regression turns](thorough-pass-2026-10-28/backend-regression.json): recorded hierarchy, identities, usage and evaluation-row linkage. |
| Signals | Six final UI turns scored; one false positive under the unchanged policy. Earlier baseline contains a correctly flagged exhausted turn. [Monitoring review](thorough-pass-2026-10-28/review.md#weave-readback-and-monitoring) |
| Setup and local checks | [310 tests/Ruff](thorough-pass-2026-10-28/local-checks.json), [zero-cache offline restore](thorough-pass-2026-10-28/fresh-setup.json), [unchanged evaluation instrument](thorough-pass-2026-10-28/instrument-check.json). Citation integrity behavior changed to contract version 3. |
| Boundaries | [Credential canaries](thorough-pass-2026-10-28/credential-sinks.json), [Markdown image browser check](thorough-pass-2026-10-28/markdown-image-after.json), [earlier publication scan](brief-e2e-v1/submission-boundary-final.json). These are bounded checks, not general security certification. |
| Public access | [Earlier anonymous publication check](brief-e2e-v1/publication.json). |

## Earlier result and comparison

The earlier measured runtime is `3a49a50`, source SHA-256 `b746d92df4edb8ecebe5729d7f26becb995ec088217b47b2e12b4a2b98952a13`. Later documentation edits do not constitute another evaluation.

| Measurement | Cases | Assertions | Basis |
| --- | ---: | ---: | --- |
| [October 27 regression](brief-final-regression-v1/summary.json) | 13/13 | 48/48 | Runtime `3a49a50`, rubric 2.3, $2.85 agent + judge. |
| [Fresh baseline](brief-e2e-regression-v1/summary.json) | 10/13 | 44/48 | Source `b269258e7786`, rubric 2.2; a separate rerun of the earlier runtime. |
| [Original tagged submission](submission-repair-regression-v3/summary.json) | 10/13 | 45/48 | Runtime `755036e`, source `b269258e7786`, rubric 2.2. Preserved by the immutable submission tag. |

Rubric 2.3 corrected two unsolicited requirements in case 03. Questions, references and the other 46 assertions stayed fixed: **43/46 baseline → 46/46 revised**. [Case-by-case comparison](brief-e2e-v1/comparison.json) separates these rubric corrections from behavior changes. Manual [answer review](brief-e2e-v1/final-answer-review.json) flags a generous hierarchy grade in case 02 and an incomplete illustrative sketch; 13/13 remains the recorded judge result, not a correctness guarantee.

## Earlier verification receipts

| Check | Evidence and scope |
| --- | --- |
| Local checks | [245 tests and Ruff](brief-e2e-v1/local-checks-final.json) on the measured runtime. These test boundaries and control flow, not general answer quality. |
| Fresh setup | [Isolated installation](brief-e2e-v1/fresh-setup-final.json): zero cached pages, all 351 bundled pages restored with network blocked, runtime imports successful. No credentials or model calls. |
| Actual app | [Final browser review](brief-e2e-v1/ui-final/manual-review.json): 4/4 questions, 12/12 task checks, $0.58, 23–45 seconds per answer. Same-context follow-up, once-only delivery, sources and analysis checked on desktop/mobile. [Message-history reproduction](brief-e2e-v1/ui-final/tracing-history-reproduction.json) uses stubs; generated SDK examples were not executed against a provider. |
| Traces and usage | [Regression backend](brief-e2e-v1/backend-final.json): 15 turns, 243 spans, 93 agent model calls. [UI backend](brief-e2e-v1/backend-ui-final.json): four turns, 82 spans, 27 calls. Hierarchy, source identity, usage and evaluation links reconciled. |
| Verifier | [Seven selected fixtures](brief-verifier-final-v1/summary.json) matched expected labels, including the captured invalid tool-history sketch. [Fixture review](brief-e2e-v1/verifier-fixture-review.json) and [scope correction](brief-verifier-final-v1/scope-correction.json) preserve the corrected six-fixture old/new tie of 6/6. These probes do not estimate accuracy. |
| Signal | [Diagnosis](brief-e2e-v1/signal-diagnosis.json): old policy falsely tagged 14 of 15 selected turns. [Revised setup](brief-e2e-v1/signal-setup.json), [six-fixture calibration](brief-e2e-v1/signal-calibration/summary.json), [15 regression negatives](brief-e2e-v1/signal-final-review.json) and [four UI negatives](brief-e2e-v1/backend-ui-final.json) show the narrower policy working on these examples. Live positive recall is unmeasured. |
| Public access | [Anonymous publication check](brief-e2e-v1/publication.json) records public repository commit `b06a508`, Agents and the final evaluation. This is evidence for that publication, not a fresh check of later documentation edits. |
| Submission boundary | [Credential/private-file scan](brief-e2e-v1/submission-boundary-final.json) found no configured keys or private material in the checked candidates. `.env` was ignored and owner-only. This is a bounded scan, not general PII detection. |

The earlier prose-based Signal policy classified assistant-reported failures, exhaustion and uncited instructions. The current policy selects recorded runtime review reasons in a server filter; see the repair review above. Both review completed turns and cannot block delivery.

## Why support verification is the default

The [historical pilot](coverage-pilot-v1/summary.json) ran six task families × two trials per policy; all 36 runs cost $9.65.

| Policy | Cases | Factual assertions | Mean agent time |
| --- | ---: | ---: | ---: |
| Off | 7/12 | 39/44 | 20 s |
| Support | 10/12 | 39/44 | 42 s |
| Support + coverage | 8/12 | 32/44 | 55 s |

Support's extra case passes came from citation integrity; factual assertions tied with off. Coverage refused two answerable tasks. [Failure review](coverage-pilot-v1/review.md) retains all 11 failed case-runs; [cost audit](coverage-pilot-v1/accounting-review-final.json) reconciles 330 unique provider requests. Six selected task families are not 36 independent tasks or a general reliability estimate.

The recorded [Compare browser check](coverage-pilot-v1/compare-ui-review.json) showed missing summary values. The later [backend readback](coverage-pilot-v1/backend-final-readback.json) reconciled all six completed summaries and 36 case scores. The rendering cause is unknown; successful offline aggregation does not establish why the UI showed N/A. Replaying completed answers or deleting their evidence would not resolve that diagnosis.

<details>
<summary>Earlier failures and supporting measurements</summary>

These records explain the repairs; their results apply to their recorded source and rubric.

| Finding | Record |
| --- | --- |
| Baseline failures and intermediate UI defect | [Baseline review](brief-e2e-v1/baseline-review.json), [initial browser review](brief-e2e-v1/ui-baseline/manual-review.json), [invalid tool-history reproduction](brief-e2e-v1/ui-repair/tracing-history-reproduction.json). Original criteria and interrupted harness evidence remain beside the outputs. |
| Focused repair before the final runtime | [Four-case run](brief-repair-focused-v1/summary.json): 4/4, 16/16 on source `8a16ba410216`; [intermediate UI](brief-e2e-v1/ui-repair/manual-review.json) still exposed a code-history defect. |
| SDK-container infrastructure failure | [Readiness run](readiness-head-20261026-v1/summary.json): zero predictions and model calls on `e4f48c7`. A failed evaluation harness, not a 0/13 answer-quality score. |
| Earlier full evaluations | [Original submission run](submission-v1/summary.json), [assertion regression](regression-v2/summary.json), repaired [v1](submission-repair-regression-v1/summary.json) and [v2](submission-repair-regression-v2/summary.json). Different versions and rubrics; do not rank them as controlled comparisons. |
| Trace transport and costs | [Original completion recovery](submission-v1/remote-recovery.json), [agent trace readback](agent-trace-readback-v2.json), [judge readback](judge-trace-readback-v2.json), [cache probe](caching-probe-v1/cache.json). A warm synthetic call reused 2,491 tokens; this is not a real-answer savings benchmark. |
| Citation, security and monitoring boundaries | [Malformed-citation replay](coverage-pilot-v1/citation-replay-v2.1.json), [credential boundary](security-boundary-check.json), [Signal filtering](signal-filter-verification.json), [historical live failure tag](coverage-pilot-v1/live-signal-review.json). These retain their original scope and policies. |

</details>

## Reading the numbers

Case success requires all assertions plus judge-quality and integrity gates. Source-check status, retrieval overlap and online tags are separate diagnostics. The judge shares the assistant's model family, and these tasks were reused during development; selected fixture passes cannot establish general reliability.

Costs are rounded estimates from returned provider usage, including repairs and evaluation judging. JSON retains exact usage, IDs and hashes. Background Signal scoring and unreturned charges are excluded unless a receipt explicitly includes them; experiment reservations are not billing caps. Raw records remain in their original folders.
