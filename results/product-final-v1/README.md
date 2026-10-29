# Final runtime validation

**Regression: 13/13 cases and 48/48 assertions. Actual UI: 17/18 outcomes and 5/6 tasks; the separate preset fulfilled its literal request.** Backend records reconcile for the regression and all eight UI turns. This packet preserves the first attempts on the all-Opus configuration; earlier repairs and selected writer/verifier probes remain separately attributed.

| Identity | Frozen value |
| --- | --- |
| Runtime commit | `dfdb6bdfff88710d1b075c9839d38917c3a38fd1` |
| Source SHA256 | `2b4c8d1b6bbf70396fb63a68dcf55361e40bb6fd735fa292c8f803ae8d46c079` |
| Measurement checkout | `6b05cf9cf67851e096b94ec6e9e844aeb2c45141` |
| Models | Opus 5.5 for planning, writing, verification, recovery and offline judging |
| Effort | Medium for agent calls; provider default for the offline judge |
| Instrument | Unchanged rubric 2.3, citation contract 3, verification contract 4 |
| Corpus / retrieval | Same 351-page October 24 snapshot and production BM25 |

[Frozen protocol](protocol.md) · [Exact UI inputs](tasks.json) · [Historical evidence](../README.md)

## Why this configuration

An Opus auditor with a Sonnet writer left the [v2 replay](../product-repair-v2/summary.json) at 16/18 outcomes and 4/6 full task passes; its separate preset did fulfill the literal question. The subsequent [writer probe](../product-writer-probe-v1/review.json) answered two selected problem questions with Opus in 68.94/35.39 seconds, costing $0.6679 combined. Its overview still missed the frozen benchmark's completed-turn timing criterion.

We chose the stronger writer before adding another fallback path. These selected successes do not establish general superiority, lower latency or a general success rate. The complete validation below retains the original questions and failure criteria.

## Regression

The [completed run](../product-final-regression-v1/summary.json) passed **13/13 cases and 48/48 assertions**, with zero failed judges, ungraded assertions or operational errors. Questions, references and rubric 2.3 are unchanged.

| Recorded measure | Result |
| --- | ---: |
| Agent turns, including earlier follow-up turns | 15 |
| Agent / offline judge calls | 88 / 13 |
| Agent / offline judge estimated cost | $3.1311278 / $1.438898 |
| Combined returned-usage estimate | **$4.5700258** |
| Median engine duration across all 15 saved turns | 33.41 s |
| Engine-duration range | 11.29–64.96 s |

The summary's 35.94-second mean describes the 13 final-turn outputs only; the all-turn mean is 36.5007 seconds. These are engine times, not actual UI waits. The remote summary synchronized without replaying the completed record; indexed-row and child-call checks are reported separately below.

[Independent Codex-assisted review](regression-review.json) inspected all 13 cases and 15 turns, matched 53 cited passage references and parsed seven Python fences, without a demonstrated material defect. The original judge scores remain unchanged. This is not held-out accuracy, human calibration or execution of generated SDK/provider examples.

One 13-case `weave.Evaluation`, including follow-up turns, with the unchanged assertions and LLM judge. The $7 reservation budget is not an account billing cap. Preserve failures and ungraded work rather than rerunning to improve the score.

## Actual app replay

All seven turns delivered complete answers. [Independent review](answer-review.json) assesses all six tasks against the original 18 criteria. The only failed criterion is the overview's omission of completed-turn Signal timing. The role comparison is useful and satisfies the literal broad question, but the frozen extra timing requirement remains failed. It is not silently removed from the benchmark.

| Seven-turn replay measure | Result |
| --- | ---: |
| Frozen outcomes / full task passes | 17/18 / 5/6 |
| Visible completed / runtime complete turns | 7/7 / 7/7 |
| Median / maximum visible completion time | 52.241 / 92.446 s |
| Median engine duration | 51.01 s |
| Model calls | 48 |
| Returned-usage estimate | **$2.032156** |

[Exact timings](summary.json) distinguish browser-observed completion from engine duration. Complex answers can exceed a minute. The follow-up retains the direct-Anthropic context, assistant/tool history and nullable cache accounting; no material code defect was demonstrated. The pinned Weave 0.54 `Turn.start_llm` API was checked statically in the [case 10 API receipt](regression-review.json), not executed with a provider. Static source/API/code inspection is not SDK integration execution.

The additional actual Understand Weave preset click fulfilled its literal question, with eight cited passages checked against the frozen snapshot and no demonstrated material defect. Its Evaluation-to-trace explanation is supported by `tutorial-eval` section 9. The answer took **76.671 seconds visibly / 74.83 seconds in the engine**, using **10 model calls and $0.4577432** estimated. This separate preset is excluded from the seven-turn totals and 18 benchmark criteria; its pass does not regrade the overview's missing timing detail. [Answer review](answer-review.json) · [Saved result](preset-smoke/result.json)

## Backend and local checks

The [regression readback](evaluation-backend-readback.json) verifies the completed evaluation parent, **13/13 indexed rows**, exact prediction/score links, **15/15 Agent roots** and **88/88 model spans**, with returned usage reconciled. Agent estimates are $3.1311278 locally and $3.13112773 remotely, differing only in rounding. Optional `scorer_call_ids` index metadata is absent; actual direct scorer records and full scores match.

[UI readback](backend-readback.json) verifies **8/8 Agent roots and 58/58 model spans**, with source identity, linkage, outputs and usage reconciled. This includes the seven benchmark turns (48 calls, $2.032156) and the separate preset (10 calls, $0.4577432): **$2.4898992 total** locally versus $2.48989914 remotely, differing only in rounding. Successful local results or raw stored calls do not alone establish evaluation indexing. No missing rows were replayed or reconstructed.

[Local checks](local-checks.json): **599 tests pass in 15.06 seconds**, with 336 SDK/Pydantic warnings; Ruff and diff checks pass. [Fresh setup](fresh-setup.json): locked install from a new checkout, no `.env`, empty document cache, all 351 pages restored with socket connections blocked, zero connection attempts and matching final source identity. Dependency package cache was allowed. No model/API calls were made by these checks.

[Preset visual checks](preset-smoke/visual-review.json) inspected the captured 1440 px desktop and 390 px mobile layouts and the Sources & analysis dialog. The answer and controls fit the viewport; the dialog opened and no browser errors were recorded. These captures are not an accessibility audit or general usability study.

[Signal readback](signal-readback.json) verifies the current active monitor and source-matching completed-turn/runtime-reason filter. [Scoring history](signal-history.json) links unchanged earlier eligible and excluded actual turns with the same monitor digest; this is not new final-run inference validation.

## Limits

These are reused development questions, reviewed with Codex assistance and a same-family LLM judge. The overview timing criterion remains despite exceeding the literal broad question. No new Claude run, retrieval arm or paid repeat for a perfect score is included. Cost estimates exclude Signal inference, hosting, taxes and unreturned charges. Earlier raw answers, grades and delivery gaps remain preserved.

[Anonymous publication check](publication.json): the public repository at `05f1759`, the Agents view and this evaluation were visible without sign-in. The evaluation rendered all 13 examples. Later receipt/link-only commits leave the measured runtime unchanged.
