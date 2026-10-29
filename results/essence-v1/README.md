# First simplification: preserved findings

Runtime `3433cd3`, source `216497c3aa9eeba6bddc26c17ffe2700255fb03bc39473c66e12289cc334efb0`, verification contract 6. Opus 5.5 writes and audits at medium effort; the offline Opus judge uses provider-default effort. Snapshot and regression rubric 2.3 are unchanged. [Frozen protocol](protocol.md)

## What changed and why

One tool loop now owns research, drafting and bounded repair. Removed the separate task-planning call, workflow-facet protocol, verifier-directed research, terminal recovery/recheck paths and SQLite answer library. The auditor gets the original question, conversation and read evidence; it reports problems and missing requested parts. It no longer reproduces every supported claim and then risks rejecting its own paraphrase.

The defect is captured in the [writer diagnostic](writer-diagnostic/review.json): a corrected Ops answer was refused solely because the auditor summarized its code instead of quoting it exactly. Other failures involved unrequested legacy-workflow scope. Both writers were affected. [Repair rationale](audit-reporting-proposal.md)

The twelve diagnostic attempts used the earlier source `2fe0b90`, contract 5. Sonnet fulfilled 2/6 planned literal tasks and Opus 5/6; the final Sonnet attempt was interrupted by a spend reservation before the next provider request. The complete six-pair rule was not established, and Sonnet also failed the quality condition. Opus remains provisional; this is not a general model ranking. Returned usage cost was **$4.76**. No source changed during the diagnostic.

## Current checks

| Check | Result and scope |
| --- | --- |
| [Local checks](local-checks.json) | 428 tests; Ruff and diff checks pass. 336 existing SDK warnings retained. Mechanical safety/control-flow/UI checks, not semantic accuracy. |
| [Auditor controls](auditor-check-v1/summary.json) | Two useful answers accepted, three substantive defects rejected, all five verdicts valid. $0.23. Selected development controls, not a reliability rate. |
| [Control review](auditor-check-v1/semantic-review.json) | Central reasons are supported. Some negative feedback still adds optional obligations or imprecise explanations. Label agreement does not make every sentence correct. |
| [Control readback](auditor-check-v1/backend-readback.json) | Five root → verifier → provider hierarchies and exact responses/usage verified remotely. |
| [Fresh setup](fresh-setup.json) | Clean clone, empty dependency cache, locked install, 351 pages restored offline, matching fingerprint; no credentials or model calls. |
| [Regression](../essence-regression-v1/summary.json) + [supplemental grade](supplemental-grade/summary.json) | 12/13 cases and 47/48 assertions after grading the one reservation-denied stored answer. Original Evaluation remains 11 passed, one failed, one ungraded. Authentication/agent-export omission remains a failure. Combined returned cost $4.30. |
| [Actual browser review](ui/answer-review.json) | 17/18 criteria, 5/6 tasks. Overview and separate preset conflate conversation display with turn scoring. Median terminal-prose time 23.282 s; one code block was not yet rendered, so this is not full-render timing. Eight turns cost $1.56. |

[Size review](size-review.json): app plus runtime package **5,458 → 3,764 physical lines**. Agent **1,806 → 886**; UI **695 → 457**. Of the 1,694 lines removed from that surface, 455 moved to experiment scripts. The rest includes deleted control-flow paths and library functionality. Physical lines alone do not measure readability; the reduced number of runtime concepts is the substantive change.

## How to read quality and speed

- A case passes the regression only when every assertion, all judge dimensions and deterministic integrity pass. Denominators stay 13 planned cases and 48 planned assertions, including missing or failed judges.
- Browser criteria are frozen at 18 across six tasks/seven turns. The overview timing criterion exceeds the literal question; preserve that score and separately assess literal fulfillment. The preset is an extra eighth turn, excluded from the seven-turn median.
- Engine time includes the whole agent loop; visible time starts at Enter/click and ends when the terminal answer is rendered. Offline judge time is excluded from agent latency. First answer text is not labeled useful without review.
- The historical baseline was 13/13 and 48/48; browser 17/18, five of six tasks, median visible wait 52.241 seconds, maximum 92.446. Those results belong to `dfdb6bd`, not this source. Historical comparisons also vary provider load and cache state.
- Partial, refused, interrupted and timed-out work remains in the record. A fast refusal to an answerable question is not a latency success.

The first pass cost $10.8437213 including the diagnostic, controls, regression, supplemental grade and UI. The [follow-up protocol](protocol.md#follow-up-after-the-first-simplified-run--october-29) records the targeted repair and revised planning ceiling before further paid work. All prior evidence and the original submission tag are preserved.

Both [regression](evaluation-backend-readback.json) and [UI](ui-backend-readback.json) delivery reconcile remotely. This does not cure the independently reviewed answer defects. The first-text observer captured progress; first useful time remains unmeasured. [Follow-up](../essence-v2/README.md) keeps these first attempts intact.
