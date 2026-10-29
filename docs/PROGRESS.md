# Progress

Updated **October 29, 2026**. This is the running status and next-work list. The [build log](AI_BUILD_LOG.md) explains past decisions; the [evidence index](../results/README.md) preserves the actual runs.

**Current state:** the smaller assistant is runnable, the brief's core components are implemented, and the funded browser check is complete. Answer omissions and long waits remain. Current measurements belong to runtime **`522c320`**, not to every later documentation commit.

## What is complete

| Area | Status and evidence |
| --- | --- |
| Agent and conversation | One bounded tool loop searches, reads, runs optional offline Python and checks drafts. Follow-up context worked in the actual browser. [Code map](CODE_MAP.md) |
| Tool-list swap | Confirmed on one historical real turn: exhausted research budget left only `submit_answer`, followed by a useful overview. It still missed one frozen criterion. No demonstrated causal benefit or live final-slot example; no trigger found in the bounded current receipt scan. [Audit](../results/essence-v2/tool-list-swap-review.json) |
| Simpler implementation | App/package reduced from **5,458 to 3,774 lines**: 455 moved to optional experiments and 1,229 removed. Separate planning, recovery and SQLite-library paths were removed. [Accounting](../results/essence-v2/size-review.json) |
| Browser quality | All seven benchmark turns delivered. **17/18 frozen checks; 5/6 strict tasks.** AI-assisted source/code review found all **six literal requests fulfilled**. The overview omits the checklist's completed-turn timing detail. [Review](../results/essence-v2/ui-after-funding/answer-review.json) |
| Preset and speed | The actual overview button worked in **30 seconds**. Seven benchmark turns had a **23-second median to terminal prose**, range **18–67 seconds**. One late code block leaves its exact full-render time unmeasured; no full-seven render median is claimed. [Measurements](../results/essence-v2/summary-after-funding.json) |
| Regression coverage | **All 13 cases assessed; judge-recorded 12/13 and 47/48 assertions**, across the original twelve assessed cases and one billing-failure retry. The original run is preserved. [Completion view](../results/essence-v2/regression-completion.json) · [Retry readback](../results/essence-v2/regression-resumption-backend-readback.json) |
| Weave tracing | All **eight browser turns and 47 provider responses** matched stored outputs, hierarchy, source identity and usage. This proves delivery, not correctness. [Readback](../results/essence-v2/ui-after-funding-backend-readback.json) |
| Online Signals | The completed-turn policy is active, with an attributed review tag on the earlier billing failure. It cannot block answers and is not a general correctness detector. [Policy](../results/essence-v2/signal-readback.json) · [Scoring evidence](../results/essence-v2/signal-error-readback.json) |
| Local checks and setup | **428 tests**, Ruff and a fresh-clone offline corpus restore passed on the measured source. Generated SDK examples were inspected, not integration-tested. [Checks](../results/essence-v2/local-checks.json) · [Setup](../results/essence-v2/fresh-setup.json) |
| Publication and notes | Public repository, Agents and evaluation pages opened without login. README and private interview guide were updated; interview preparation stays outside Git. [Public-access check](../results/essence-v2/publication-after-funding.json) |

## What is still open

| Issue | Current evidence | Next useful action — not started |
| --- | --- | --- |
| Initialization answer is incomplete | Regression omitted authentication and agent-span export; the auditor accepted it. | Follow the omission through retrieved evidence, drafting and verification; test a general correction against both valid and incomplete answers. |
| A judge pass can hide an omission | The resumed case correctly answers the literal question, but the judge passes its hierarchy assertion despite missing explicit LLM/tool nesting. [Independent review](../results/essence-v2/regression-resumption-review.json) | Calibrate the judge against source-grounded positive and incomplete examples; preserve the recorded disagreement. |
| Long waits and auditor value | One browser answer took 67 seconds. Four captured-answer controls identified neither targeted negative defect in their reasons. [Control review](../results/essence-v2/auditor-check/semantic-review.json) | Compare the model audit with deterministic citation checks on matched tasks before adding checking machinery; measure completion, wait time and cost together. |
| Evidence has limited reach | Reused tasks, same-family agent/judge and a stored October 24 snapshot. No live documentation refresh or SDK-compatibility check. | Keep these limits visible; use held-out tasks and independent reviewer calibration for broader claims. [Version contract](VERSIONING.md) |

Voice, adaptive UI, graph retrieval and additional specialists remain deferred. Hybrid search remains experimental: its measured retrieval gain missed the adoption threshold and did not establish better answers. [Comparison](../results/retrieval-comparison-v1/README.md)

## Dated updates

- **October 29 — checked whether the tool swap was ever used.** One read-only Weave query confirmed the historical research-budget branch with three planning calls left. The final submission was useful, but this does not show the swap rescued it. Current implementation tests cover the reduced tool list; the final-slot trigger’s live benefit remains unestablished. [Trace, source and review evidence](../results/essence-v2/tool-list-swap-review.json)
- **October 29 — regression coverage completed.** At the owner’s request, reran only the billing-blocked case with the same runtime, question, references and rubric. Cost **$0.36** beyond the completed simplification pass. All thirteen cases now have grades across the two runs: **12/13 recorded passes, 47/48 assertions**. The initialization failure remains; independent review also flags generous hierarchy grading on the retry. [Completion and original-attempt links](../results/essence-v2/regression-completion.json)
- **October 29 — funded validation finished.** Resumed the frozen runtime after credit was restored. Completed seven benchmark turns plus the preset, reviewed the answers and reconciled Weave delivery. Browser cost was **$2.10**; the pass's known usage estimate reached **$17.83** against the original $18 estimate. Signal inference and unreturned charges are excluded. This pass then stopped; the later separately requested regression retry is recorded above. [Receipt](../results/essence-v2/summary-after-funding.json)
- **October 29 — browser measurement repaired.** A timer stopped before a code wrapper appeared. Preserved that attempt, corrected the observer and passed six unpaid instrument controls. The answer was not regenerated to replace the timing failure. [Controls](../results/essence-v2/observer-v3-proof.json)
- **October 29 — program simplified.** Removed extra planning, recovery and library machinery; kept the brief's agent loop, verification, tracing, Signals and evaluation. Current and historical scores remain separate. [Validation packet](../results/essence-v2/README.md)
- **October 25–28 — build and earlier experiments.** Implemented the core brief, compared verification policies, repaired real failures and tested retrieval alternatives. The work exceeded the approximately three-hour brief. [Dated build history](AI_BUILD_LOG.md)

Keep the current status and next actions up to date after meaningful changes. Add a dated entry with **what changed → what was verified → evidence → what remains**. Preserve old results, distinguish proposed work from completed work, and attach new measurements to their actual runtime and rubric.
