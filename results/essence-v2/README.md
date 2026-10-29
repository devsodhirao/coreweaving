# Simplified assistant: final validation

Runtime `522c32006389806149ea177564a5e45c7286cd92`, source `bd74bb83b9fd34273acb50edcec66ea4ba0a5cf865ae867b2fc04cd84229a839`. Opus 5.5 writes and audits at medium effort; Opus judges at provider-default effort. Verification contract 6, citation contract 3 and regression rubric 2.3. Questions, references, assertions and browser criteria are unchanged.

This pass keeps one conversational tool loop, one source/task auditor, bounded repair, Weave tracing, Signals and evaluation. It removes separate task planning, workflow facets, verifier-directed research, terminal recovery and the SQLite answer library. App/package size is **5,458 → 3,774 physical lines**: 455 moved to optional experiment scripts and 1,229 removed. [Size accounting](size-review.json)

## Product results

| Check | Observed outcome |
| --- | --- |
| [Regression](../essence-regression-v2/summary.json) | **11 passed, one incomplete, one billing-blocked case**, out of 13 planned. **44/48 assertions passed**: one failed and three were ungraded. |
| [Answer review](regression-review.json) | All 13 cases/15 turns inspected. Initialization remains useful but omits authentication/agent-span export. No substantive answer was produced for the last case after provider rejection. 47 documentation citations and one execution record matched their sources. SDK examples were not integration-tested. |
| [Availability diagnosis](provider-failure-readback.json) | The failed planner request returned HTTP 400 for insufficient Anthropic credit. The later judge request was withheld by the experiment budget's error stop. This is an availability failure, not a wrong substantive answer or a tool-protocol defect. |
| [Timing and spend](summary.json) | All 15 engine turns: median **20.06 s**, range **8.36–56.13 s**, including the failed request. Fourteen substantive answers: median **22.005 s**. 85 agent invocations, 84 actual agent responses. Known regression estimate **$4.32**, with no usage returned for the rejected request. |
| [Funded browser replay](ui-after-funding/answer-review.json) | **17/18 frozen criteria; 5/6 strict tasks. All six literal requests fulfilled** in AI-assisted source/code review. The overview omits the frozen completed-turn timing detail. Seven-turn terminal-prose median **23.383 s**, range **18.242–66.504 s**; one full-render time remains unmeasured. |
| [Preset and browser delivery](ui-after-funding-backend-readback.json) | Actual **Understand Weave** button returned a useful answer in **29.575 s** to matching render. Eight root turns and 47 provider responses match outputs, source identity, parentage and usage. All 34 documentation-citation occurrences match the corpus. SDK examples were inspected, not executed. |
| [Remote evaluation readback](evaluation-backend-readback.json) | All 13 rows/scores and 15 Agent roots match. 84 agent responses and 12 judge responses match usage; the failed planner ERROR span is verified separately. The withheld judge has no provider response. |

The [frozen protocol and bounded final recheck](../essence-v1/protocol.md) preserve every first attempt and the unchanged questions and quality criteria. After funding resumed, the eight browser turns cost **$2.10**, bringing the pass’s known usage estimate to **$17.83** against the original $18 estimate. The earlier rejected request returned no usage; Signal inference and unreturned charges are excluded. The conservative browser receipt stop paused before the preset; the [one remaining planned click](preset-resumption.json) fit the remaining allowance using the observed same-question cost. No further paid work followed. [Current accounting](summary-after-funding.json) preserves the [funding-blocked record](summary.json).

The [first simplified pass](../essence-v1/README.md) remains preserved, including its initialization omission, overview scope defect and incomplete code-render timing. Its seven-turn terminal-prose median was 23.282 seconds; the older `dfdb6bd` UI median was 52.241 seconds. Different source, provider/cache conditions and code-readiness methods prevent treating that as a causal final speed improvement. The current seven-turn terminal-prose median is **23.383 seconds**, while the tracing sketch took **66.775 seconds** to matching render. Its extra research repaired a source-support gap; it did not demonstrate correction of a false API claim. These are observations, not an isolated causal speed gain.

**Assessment:** the smaller program retains the brief’s core features, completes the browser requests and now has verified delivery on the frozen runtime. It still misses an initialization detail in regression and can take over a minute on a complex answer. The browser review separates literal fulfillment from the stricter checklist; it does not turn 17/18 into 18/18 or replace the earlier billing-blocked regression case. A green verifier badge is not a correctness guarantee.

## Does the auditor detect the intended defects?

Four captured/corrected controls produced four valid verdicts, accepted both positives and rejected one negative. **Neither targeted defect was identified in the reasons.** The initialization omission was accepted; the overview was rejected for different, partly debatable reasons also present in its accepted corrected partner. Three of four matching labels therefore do not demonstrate a repaired verifier. The init fixture adds the same authentic quickstart passage to both candidates; it tests auditing with evidence available, not improved retrieval.

[Original frozen fixtures](../essence-v1/scope-controls.json) · [Fixture fairness review](../essence-v1/scope-controls-review.json) · [Four-call results](auditor-check/summary.json) · [Semantic review](auditor-check/semantic-review.json) · [Backend identity, verdict and usage readback](auditor-check/backend-readback.json)

The earlier compact-audit runtime passed five selected controls. Neither set is independent human calibration or a general accuracy estimate. No extra control reruns were selected to make the score green.

## What the measurements mean

- Regression counts all 13 planned cases and 48 assertions. Fifteen turns include both turns of the two follow-up cases. Judge errors remain distinct from answer failures.
- Browser quality preserves all 18 frozen criteria across six tasks/seven turns. Literal fulfillment is reviewed separately. The actual overview button is an additional smoke test, outside that seven-turn median.
- Engine time stops when the agent returns; offline judging is excluded. Terminal-prose time requires visible answer text, enabled input and Sources & analysis. Observer 2 stopped before the paraphrase’s code wrapper mounted; its original timing remains preserved but unvalidated. Observer 3 captures continuous candidates and selects the earliest 250-ms-stable snapshot matching exact exported prose/code, captured before opening analysis. Six of seven benchmark render times are validated; a full-seven render median remains unmeasured.
- Progress text does not count as an answer. First useful answer time is unmeasured. DOM readiness is not a browser-paint measurement. Older timers did not reliably wait for code, so historical timing comparisons are descriptive and method-qualified.
- All trials are reused development tasks, one current pass each. Same-family review can miss shared mistakes. No model ranking, general reliability or causal speed percentage follows from these samples.

[Earlier observer controls](render-measurement-proof.json) · [Six repaired-observer controls](observer-v3-proof.json) · [428 local tests and Ruff](local-checks.json) · [Fresh clone, clean install and 351-page offline restore](fresh-setup.json)

The [freshly read-back Signal policy](signal-readback.json) is unchanged. The current billing-failed turn received one [attributed needs-review tag](signal-error-readback.json) from the configured monitor. The trace identifies the billing cause; the tag only establishes that operational review ran. It cannot block delivery and can miss factual errors on turns the runtime marks complete. [Earlier scoring history](../product-final-v1/signal-history.json) remains preserved.

## Reading the public Weave pages

[Anonymous access check](publication.json) verified the published repository, Agents dashboard and current Evaluation, including all 13 example rows. Its `passed` value is 11/13 (84.6%); `output.task_complete` is the assistant's own 12/13 label and misses the initialization omission. The displayed mean assertion fraction (0.972) averages graded case fractions; it is neither the pooled 44/45 graded assertions nor 44/48 planned assertions. Its mean final-output time (26.84 s) also differs from our all-15-turn median (20.06 s). These are different aggregations, not interchangeable quality or speed scores.

The Conversations list labels several successful conversations `source_verifier`. A [bounded span check](conversation-label-readback.json) found the root still named `coreweaving`, with explicitly named verifier children and correct parentage. The list's label-selection rule remains unknown; the observed display alone does not establish a tracing defect or vendor bug.
