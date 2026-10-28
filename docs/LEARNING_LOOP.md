# How the evidence helps us improve

The records help explain what happened, why a check accepted or rejected an answer, and what a repair changed. Their value depends on whether they lead to better decisions. Product success still means people can complete useful documentation tasks accurately, with understandable limitations and acceptable time and cost. Collecting traces does not establish that outcome.

*Working note, October 28: the first focused workflow-facet acceptance failed at verdict delivery. A delivery repair and further acceptance are separate work; no final success is claimed here.*

## Where it changed a decision

The strongest evidence is where the records contradicted our confidence. The [captured overview](../results/thorough-pass-2026-10-28/ui-final/01-overview.json) passed source checking while explicitly declining to compare Signals timing with evaluations. Its cited statements could be supported while the user's comparison remained unfinished. This exposed the distinction between checking claims and completing the requested task.

The later `2adf56b` replay showed that adding outcome IDs was insufficient. One outcome bundled inputs, timing and outputs; the verifier marked it answered using a generic “Trace first” clause although the completion event was still missing. The next change split broad workflow comparisons into separate input, execution-trigger and output checks. Fixed IDs prevent dropping an assessment, and literal evidence anchors establish where text came from. Neither mechanism proves that a quote answers its assigned question. Focused questions should retain their narrower scope.

The [first focused probe](../results/task-completion-repair-v1/workflow-probe/manual-review-v1.json), on `2033cec`, then exposed a delivery failure. The live planner correctly selected three subjects and nine facets. The negative verdict reached its 4,000-token output limit, leaving no valid outcome or research-request result. The positive verdict marked all nine facets answered but omitted every required evidence anchor, so the runtime rejected it. This was not a successful semantic negative-control test, nor evidence that the positive answer lacked source support. A correct design and passing fake-model tests did not establish that the real model could deliver the contract within its limits. Preserve this failed acceptance even if a later delivery repair succeeds.

The Signal failure exposed another boundary. Its LLM flagged the cited arithmetic answer while acknowledging citations. Moving eligibility into a server query removed that prose judgment from selection: recorded runtime failure/completion reasons determine eligibility, and the LLM explains selected turns. Five synthetic fixtures selected exactly the two intended cases and excluded three controls. That establishes the filter and worker path for those fixtures. It does not establish that the application always assigns the correct reason or that every eligible turn receives a useful explanation.

The first six frozen verifier probes also caught a false rejection of the complete overview. The model supported its claims and marked all outcomes answered, but the runtime rejected a quote that omitted citations before the final period. Another quote inserted a word, which should remain invalid. This supports a narrow protocol repair, not approximate paraphrase matching. The batch also accepted shared API semantics documented on an integration page and rejected an unsupported extension of integration behavior to every Python application. Positive controls matter as much as catching omissions.

## Is this reinforcement learning?

This is “kind of like reinforcement” only in the everyday sense that feedback influences our next decision. Currently it is observability, curated feedback, regression testing, and human-directed policy/code iteration. We are not updating model weights, optimizing a learned policy against rewards, or automatically promoting successful answers into memory. A green score is a fallible measurement, not a training signal the system independently learns from. Calling this reinforcement learning would overstate what exists.

## What to keep measuring

The useful loop is straightforward: preserve the question, answer, evidence, actions, runtime identity, judgment and cost; identify a failure mechanism; freeze a reproducer and a legitimate positive control; make a bounded change; inspect improvements and regressions. Verify output delivery before interpreting semantic judgments. Keep failures, refusals, partial answers and slow paths alongside successes. More checks or a rising development score are not progress by themselves. Avoid accumulating prompt exceptions for individual questions or rerunning examples until they pass.

[Historical rubric corrections](AI_BUILD_LOG.md) deserve the same honesty. Two unsolicited requirements were removed in rubric 2.3, with old results and common assertions preserved. That can improve measurement fairness, but the resulting pass is not a runtime improvement. The reused 13-case suite is a development regression set. Its judge also shares the assistant's model family. Agreement among these checks is not independent confirmation of truth.

A stronger improvement claim needs untouched tasks and paraphrases selected before inspection, fixed criteria, answerable positives and misleading negatives, and repeated runs when variability matters. Measure complete user journeys alongside isolated verifier decisions. Track unnecessary refusals, missing requested parts, citation support, latency, research/rewrite counts and total cost under comparable budgets. Separate Signal costs where known. A holdout becomes development data once its failures guide tuning.

The evidence loop is useful engineering infrastructure. It is not yet evidence of autonomous learning or broad reliability. Use it to make explainable decisions, including removing complexity, rather than as a directive to build another learning subsystem.
