# Evidence index

Start with the [end-to-end review](brief-e2e-v1/review.md) for findings and this index for the underlying receipts. Recorded answers, failed attempts and labeled fixtures remain unchanged.

## Current result and comparison

The measured runtime is `3a49a50`, source SHA-256 `b746d92df4edb8ecebe5729d7f26becb995ec088217b47b2e12b4a2b98952a13`. Later documentation edits do not constitute another evaluation.

| Measurement | Cases | Assertions | Basis |
| --- | ---: | ---: | --- |
| [Current regression](brief-final-regression-v1/summary.json) | 13/13 | 48/48 | Runtime `3a49a50`, rubric 2.3, $2.85 agent + judge. |
| [Fresh baseline](brief-e2e-regression-v1/summary.json) | 10/13 | 44/48 | Source `b269258e7786`, rubric 2.2; a separate rerun of the earlier runtime. |
| [Original tagged submission](submission-repair-regression-v3/summary.json) | 10/13 | 45/48 | Runtime `755036e`, source `b269258e7786`, rubric 2.2. Preserved by the immutable submission tag. |

Rubric 2.3 corrected two unsolicited requirements in case 03. Questions, references and the other 46 assertions stayed fixed: **43/46 baseline → 46/46 current**. [Case-by-case comparison](brief-e2e-v1/comparison.json) separates these rubric corrections from behavior changes. Manual [answer review](brief-e2e-v1/final-answer-review.json) flags a generous hierarchy grade in case 02 and an incomplete illustrative sketch; 13/13 remains the recorded judge result, not a correctness guarantee.

## Verification receipts

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

Signals classify assistant-reported operational failure, explicit research-limit exhaustion, or factual setup instructions with no source marker. They review completed turns; they do not verify factual correctness or block delivery.

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
