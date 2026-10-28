# Task completion repair

The starting defect was an answer that passed source verification while omitting a necessary part of the question. The overview preset explained tracing, evaluations and Signals without establishing when a Signal scores a turn. Rephrasing the answer did not recover that missing premise.

## What changed and why

| Mechanism | Purpose | What it cannot prove |
| --- | --- | --- |
| Freeze requested outcomes before retrieval | Keep a repair from silently dropping part of the user's task. | The planner can still misunderstand the request. |
| Give broad workflow comparisons separate input, execution-trigger and output checks | Prevent a generic overview sentence from satisfying several different obligations. | A model still judges semantic fulfillment. |
| Anchor assessments to answer text and read evidence | Make the auditor's reasoning inspectable; reject invented evidence or omitted assessment fields. | Literal quotations alone do not establish that a conclusion follows. |
| Execute typed research requests through existing tools | Resolve a missing premise before rewriting a rejected answer. | Retrieval can still miss relevant passages. |
| Preserve incompleteness beside checked partial facts | Distinguish useful supported content from a completed task. | A partial answer is not success on the whole question. |
| Filter Signals using runtime outcomes | Select recorded failures without asking a classifier to infer them from prose. | Incorrect runtime labels remain monitoring blind spots. |

The external questions and rubric remain frozen. This changes the assistant's release policy, not the definition of a passing evaluation case. The historical source-only verification pilot is a different policy.

## Attempts retained

| Attempt | Result | Interpretation |
| --- | --- | --- |
| Literal-quote protocol, `0855b94` | [4/5 decisive fixtures](verifier-probe/manual-review.json); a valid quotation without citation markers was rejected. | Quote normalization needed to match the rendered citation convention without changing words or code. |
| Citation-only normalization, `320fd8f` | [5/5 decisive fixtures](verifier-probe/live-v2/summary.json). | Selected examples passed; later local negative tests preserved word boundaries and code whitespace. |
| Actual app, `2adf56b` | [5/6 tasks, 17/18 checks](ui-intermediate-2ad/manual-review.json), $1.25; median 65 seconds. | The overview still omitted Signal completion timing. Its broad bundled outcome was incorrectly marked complete. |
| Regression, `2adf56b` | [Seven graded cases, 25/25 graded assertions](intermediate-2ad-accounting.json); six judge failures left 23 assertions ungraded. | A provider timeout stopped further budgeted calls. This is an incomplete measurement, not a 7/13 quality result. |
| Independent workflow facets, `2033cec` | [Focused acceptance failed](workflow-probe/manual-review-v1.json), three calls, $0.16. | Planning produced nine facets. One verdict truncated; the positive control omitted every required evidence quote. Both were rejected by runtime validation. |
| Tolerant observational fields, `5d719e3` | [UI 5/6, 16/18](ui-intermediate-5d/manual-review.json); [regression 12/13, 46/48](../task-completion-regression-v2/summary.json). | Research and submissions shared one counter, leaving no revision slot after gathering evidence. Separately, an auditor-record error reduced a complete draft to partial facts. |
| Separate research/revision limits, `f4c7618` | [UI 6/6, 18/18](ui-final-f4/manual-review.json), $1.09; [regression 12/13, 43/48](../task-completion-regression-v3/summary.json), $3.20. | The original overview retrieved missing timing evidence and revised successfully. The usage follow-up found the correct passage but hit the planner output cap before submitting. |

The last failure concerns delivery of the audit contract, not evidence that the positive control is wrong. A contract that the model cannot reliably return also harms the user experience; rejecting malformed output is necessary but insufficient.

## Audit delivery correction

The next [three-call probe on `a8aafb6`](workflow-probe/manual-review-v2.json) correctly rejected the unchanged incomplete overview and returned a typed request for its missing execution trigger. The positive control contained all nine valid evidence anchors but added unused `scope_reason_note` fields, which the exact-key parser rejected. This was another protocol failure, not an unsupported answer. Required evidence validation must coexist with tolerance for unused annotations; action-tool permissions remain exact.

An [offline replay](workflow-probe/offline-replay-live-v2.json) of those same returned payloads through the corrected parser accepted the positive and retained the negative's repair request. This replay made no model calls. Required fields, literal evidence anchors and typed research permissions stayed enforced.

The `f4c7618` scheduling change lets 18 research dispatches coexist with the existing ten planning calls and two draft revisions. Submitting a draft no longer consumes a research slot. One existing terminal judge call can also recheck a complete answer after a narrowly classified auditor-record failure, instead of immediately reducing it to partial facts. It uses normal support and outcome gates. Neither the six browser turns nor the fifteen regression turns exercised that terminal path; its evidence is offline control-flow tests.

## User-facing result on `f4c7618`

All six browser journeys passed their frozen 18 checks. All 29 cited documentation passages matched the stored corpus. Desktop/mobile sources and the separate analysis panel worked. The overview's repair used new source evidence rather than repeating the rejected draft.

Latency remains poor: **31–121 seconds, median 49 seconds**, with answers of 304–413 words. Generated SDK snippets were not executed against the SDK; the tracing example only passed a fake message-history replay, and an alternative scoring snippet retained a field-mapping issue from its source example. These are reasons to keep manual product review alongside source checks.

The subsequent regression completed all 13 predictions and judges, with no ungraded assertions. Its only failed case was the context-dependent token-usage follow-up. Correct context and the exact relevant passage were present; the provider stopped at 2,400 output tokens before producing a complete submission. It is a delivery failure, not a retrieval miss. The recorded 12/13 and 43/48 remain unchanged.

## Final delivery repair on `fe4b7b5`

One truncated planner response may now retry with 4,800 tokens using the next existing planning slot. The truncated content never enters history or dispatches tools, and a successful response still passes normal verification. A second truncation or final-slot truncation stops explicitly. This does not increase the ten-call turn allowance or introduce a new recovery model.

The [unchanged regression](../task-completion-regression-v4/summary.json) completed **12/13 cases, 47/48 assertions**, costing **$3.32** across 116 agent/judge calls. Case 10 actually exercised the retry: 2,400-token truncation → 4,800-token request → completed response → ordinary audits and release. All existing questions, references, assertions and judge definitions remain unchanged. The [two-turn browser check](ui-followup-fe4/manual-review.json) passed its five assertions in 47 and 81 seconds, $0.35 total, without invoking the retry.

The remaining case 06 failure is narrow: an appropriate clarification added unsourced product alternatives. The judge's stronger interpretation that this proved API equivalence is not established by the answer. Manual review also found a real span-hierarchy overgeneralization in passing case 02. [Independent review](regression-v4-independent-review.json) preserves both findings without changing grades. No broader reliability or speed gain follows from one retry success.

[479 tests and Ruff](local-checks-retry.json), [fresh offline setup](fresh-setup-retry.json) and the [unchanged evaluation instrument](instrument-retry.json) passed. No live turn exercised the strict terminal full-answer recheck. Its evidence remains local control-flow tests.

## Final remote-delivery boundary

[Backend readback](backend-retry.json) verifies all 17 current Agent turns, including identities, nesting, model/tool calls and returned usage. It also verifies the evaluation parent and matching summary. **Only 2/13 evaluation rows were present after flush**; sampled [exact-ID requests](backend-retry-missing-rows-diagnostic.json) confirmed missing underlying calls. The local predictions and judge records are complete. A successful parent sync is not evidence that every child was delivered. The earlier fully linked `f4c7618` readback remains available.

All 17 current turns had positive runtime completion labels, so none qualified for the configured Signal and none received feedback. This is expected filter behavior, not proof that those answers were correct: independent review identified the semantic errors above. The preceding run's one recorded failure was selected and tagged correctly.

## Trace and monitoring checks

[Intermediate readback](backend-intermediate-2ad.json) reconciled all six UI traces. Seven regression roots and the evaluation linkage remained unverified after the connection failure; those gaps are retained explicitly.

The [current Signal filter](signal-setup.json) selected both eligible synthetic fixtures and excluded all three controls in the [live readback](signal-live-readback.json). Across fourteen available intermediate roots, the one recorded incomplete answer received a tag and thirteen `none` reasons were excluded. The timing-incomplete overview was one of those exclusions: the filter worked as configured while the upstream completion judgment was wrong.

## Measurement boundaries

These are development tasks and selected probes. Costs are estimates from returned usage; the failed regression also contains one unpriced provider attempt. No general reliability, speed improvement or isolated model-verifier benefit follows from these records. [Preservation manifests](focused-probe-preservation.json) retain original receipt hashes and [intermediate answers](intermediate-2ad-preservation.json).
