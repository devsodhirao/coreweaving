# Current-build regression: interrupted by a judge timeout

This attempt does **not** provide a quality score. It used runtime commit
`a07e5da`, source `b312a2c9a081`, and the unchanged 13-case / 48-assertion
regression. The first case in the frozen order generated an answer, but its
evaluation judge timed out. No valid grade was returned. The spending guard then
withheld all remaining provider requests because that request's usage was unknown.

The resulting 13 failed case records are operational failures, not evidence that
13 answers were wrong. All 48 assertions remain ungraded. The first case was
`09-fake-signal-scope`; its answer and five successful provider responses remain
saved. Known returned-usage cost is **$0.24075**, plus unknown usage from the
timed-out judge request. We cannot reconstruct its charge from these records.

The budget receipt records `APITimeoutError`; the traced judge adapter reports a
wrapped `RuntimeError` after 50.13 seconds. The underlying network/provider cause
is unresolved. The run's wall-clock duration also includes long delays outside
the model calls and is not an answer-latency measurement.

One explicit full retry, `presentation-regression-retry-v1`, keeps the same
runtime, dataset, rubric, seed and model settings. It has a $7 estimated allowance
and preserves this attempt. There were no valid quality grades to select around,
and no runtime or prompt changes were made. The retry will not replace or amend
these original records.

Read-only [backend inspection](evaluation-backend-readback.json) matched the
Evaluation parent, all 13 indexed rows and the five successful agent responses.
Agent delivery is incomplete: only 7 of 15 recorded turn roots were found. A
[follow-up query](missing-root-followup.json) for one missing conversation still
returned no spans. The cause is unresolved. Budget-denied invocations also have
no provider response IDs; they must not be counted as successful model calls.
This failed attempt is not fully verified remotely.

[Frozen protocol](protocol.md) · [Preflight](preflight.json) ·
[Original summary](summary.json) · [Retry](../presentation-regression-retry-v1/README.md)
