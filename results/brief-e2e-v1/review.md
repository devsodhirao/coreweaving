# End-to-end review

Runtime **`3a49a50`**, source **`b746d92df4ed`**, stored documentation **`4db7c17b2869`**, rubric **`2.3-task-aligned-assertions`**. This review follows the owner's request to rerun the actual application, question the tests and fix failure causes systematically.

## Outcome

- **13/13 regression cases, 48/48 assertions**, no judge errors; **$2.85** agent + judge estimate. [Exact run](../brief-final-regression-v1/summary.json) · [Independent answer review](final-answer-review.json)
- **4/4 browser journeys, 12/12 task checks**: overview, contextual follow-up, tracing and evaluation. All four delivered and saved once; actual follow-up history retained. [Browser review](ui-final/manual-review.json)
- **245 local tests pass**, Ruff clean. A new clone restored **351 pages / 3,569 passages offline** with no cached documents or credentials. [Local checks](local-checks-final.json) · [Fresh setup](fresh-setup-final.json)
- Final UI answers took **22.7–44.5 seconds** and contained **340–383 words**. They remain slow and longer than intended. One replay is not a latency benchmark.

The README maps every brief requirement to its purpose, named implementation and observed evidence. Email submission and interview rehearsal remain owner actions.

## What failed, and the general correction

| Finding | Cause and correction | Evidence / remaining limit |
| --- | --- | --- |
| Evaluation versus monitoring answer lost the comparison | Mixed-concept searches never read the Evaluation premise. The planner now researches each requested outcome with focused queries and retains the direct answer through repair. | [Baseline case 05](baseline-review.json) → [final case review](final-answer-review.json). BM25 was unchanged; no embedding benefit is implied. |
| Sampling follow-up lost its requested steps | The verifier treated reasonable application of a documented fraction/filter as unsupported; repair removed the useful answer. Permit deductions from explicit premises while rejecting invented premises. | [Baseline case 11](baseline-review.json) → final review. Support checking still cannot enforce whole-task completeness. |
| Source-checked code had invalid tool history | The generated sketch appended a tool result without an assistant tool call. Specify that general invariant, and ask for code only at the scope needed by the question. | [Captured failure](ui-repair/tracing-history-reproduction.json); [final sketch reproduced with stubs](ui-final/tracing-history-reproduction.json). This does not execute generated integrations against real APIs. |
| Case 03 punished unrequested content | Two assertions demanded optional Signal controls and an unsolicited fallibility caution. Correct those two rules in a new rubric; keep required fields, all questions/references and the other 46 assertions. | [All 13 fairness review](../../docs/EVALUATION_DESIGN.md). Its baseline setup procedure was already sound; a better case 03 score is not evidence of a runtime fix. |
| Online Signal mislabeled normal answers | Its description left room for unrelated quality judgments. Define exactly three conditions, exclusions and evidence required for a tag. | Baseline: 14 false positives; targeted calibration and final live readback below. |
| A probe itself was unfair | One fixture asked about editing an existing Signal but supplied only creation evidence. Correct it and rerun old/new policies, retaining the first confounded result. | [Fixture review](verifier-fixture-review.json): the clean paired probe tied 6/6. |

No test-specific answer table, new retrieval model, expanded permission or disabled citation guard was added. Required task details remain required. The changed guidance targets evidence gathering, valid inference, repair preservation and valid code structure across questions.

Manual review also found a generous final case 02 hierarchy grade: it lists LLM/tool activity but leaves their nesting within turns implicit, similar to an earlier failed answer. Its signature-only code sketch lacks initialization and cleanup; the answer explicitly directs readers to the lifecycle patterns before using it. The recorded judge pass is preserved; this is a judge-consistency and example-completeness limitation, not a hidden rescore.

## Is the verifier any good?

**It is a useful source gate, with observed judgment errors.** The deterministic portion rejects malformed, unknown, unread or mismatched source references. The model portion checks whether read passages support material claims. Those are different guarantees.

The historical pilot found **39/44 factual assertions with verification off and 39/44 with support checking**. Support's three extra case passes came from citation integrity. Coverage checking refused two answerable tasks, so support remains the default. These six selected questions do not establish a general reduction in hallucinations.

Live review exposed both false rejection of reasonable deductions and false acceptance of invalid generated code. The current policy matched **7/7 selected draft labels**: three supported deductions, three fabricated claims and the captured bad sketch. The corrected old/new six-fixture comparison tied **6/6**; it provides no measured improvement. [Final probe](../brief-verifier-final-v1/summary.json) · [Scope correction](../brief-verifier-final-v1/scope-correction.json)

The pilot compared verification off with citation checks plus a model audit; it had no citation-checks-only arm. It therefore does not isolate the model auditor’s added value or show that its latency is justified. The next verifier experiment should compare those two policies on held-out, manually reviewed tasks.

Keep support verification for source integrity, and judge usefulness separately. A “source check passed” label is not proof of correctness, completeness or SDK compatibility. Claims of broad accuracy would require new held-out tasks, more trials, reviewed labels and a judge from another model family.

## Comparable measurements

| Run | Runtime / rubric | Cases | Assertions | Estimate |
| --- | --- | ---: | ---: | ---: |
| Tagged submission baseline | `755036e` /2.2 | 10/13 |45/48 |$2.56 |
| Fresh unchanged-runtime replay | source `b269258e7786` /2.2 |10/13 |44/48 |$2.40 |
| Focused repair: 03, 05, 11, 13 | `3e76781` /2.3 |4/4 |16/16 |$1.19 |
| Final full run | `3a49a50` /2.3 |13/13 |48/48 |$2.85 |

The common 46 unchanged assertions scored **43/46 before, 46/46 after**. Per-case outcomes and exact identities are in [comparison.json](comparison.json). The final source changed planner/verifier policies together; this single reused development run cannot isolate their causal contributions. Historical records and the published submission tag are unchanged.

Case 13's quoted user instruction is not a retrieved-document injection attack. Case 10 has a conditional cache-accounting assertion gap, documented for future suite design. Exact reference recall is diagnostic: a valid alternate passage can support an answer.

## Actual interface

The intermediate repair replay passed 11/12 task checks but exposed the invalid generated history. The final replay passed 12/12 under the same preregistered task-aligned criteria. The earlier browser baseline used a different instrument and lost its uninterrupted follow-up after a test-harness interruption; its 9/11 exercised checks are retained without claiming a paired quality comparison. [Criteria correction](ui-baseline/criteria-review.json)

Sources open beside answers; analysis keeps original passages, checks, usage, versions and Weave links. Keyboard operation, mobile layout, once-only saving/rendering and the actual controls were exercised. Offline stubs checked the exact tracing sketch's message sequence. The evaluation sketch remains explicitly unexecuted and uses named placeholders. [Final browser and code evidence](ui-final/manual-review.json)

Final UI cost was **$0.58**; median response time **41.1 seconds**. A regression ran concurrently, so differences from earlier replay timings are observations, not a controlled speed experiment. No unverified draft was displayed. Voice and adaptive interfaces remain deferred.

## Online monitoring

The old Signal produced 14 tags on 15 baseline turns. Review against its own three-condition policy labeled all 14 false positives; the remaining turn was a true negative. Source payloads retained citation markers. Sampled scorer Calls could not be retrieved, so exact worker-rendered inputs remain unknown. [Diagnosis](signal-diagnosis.json) · [Baseline policy labels](baseline-review.json)

The revised prompt asks for a tag only for an assistant-reported operational failure, explicit limit exhaustion, or factual Weave instructions with no `[S#]` marker. It excludes cited answers, valid clarifications, false-premise corrections and quoted hypothetical failures. Six fixtures—three negatives and three positives—matched expected labels; selected examples do not establish general precision/recall. [Fixture manifest/results](signal-calibration/summary.json)

The new monitor was activated with the existing agent-name filter and completed-turn trigger. All 15 final regression turns and all four final UI turns received one empty score array each, correctly matching their policy-negative labels. [Turn-by-turn regression policy review](signal-final-review.json). [Setup](signal-setup.json) · [Live UI feedback](backend-ui-final.json) · [Full-regression readback](backend-final.json)

The Signal uses CoreWeave's Llama inference; it is separate from the Anthropic source verifier and offline judge. Source support, whole-task usefulness and operational review are separate questions. Exact asynchronous worker prompts remain unavailable through the backend Call read, even when feedback is visible.

## Trace and publication evidence

[Regression readback](backend-final.json) checks all 15 turns, 243 spans and 93 model calls, parent hierarchy, versions, model-call usage, evaluation linkage, completed evaluation rows and remote summary. [UI readback](backend-ui-final.json) reconciles four turns, 82 spans and 27 model calls with their delivered answers and $0.5800156 usage estimate.

[Artifact inspection](artifacts/review.json) covers the plan, research and walkthrough at desktop/mobile sizes with real controls and screenshots. Private interview material stays in the separate owner folder. The [submission-boundary scan](submission-boundary-final.json) checks configured credentials, outgoing Git objects and private-file exclusion; it is not a general security audit.

## Costs and remaining decisions

This review's listed model calls total **$8.40**, including baseline, intermediate failures, verifier probes, three browser replays, the final regression and explicit Signal calibration. [Itemized estimates](comparison.json) use returned usage; background monitor scoring, unreturned charges, hosting, tax and earlier sessions are excluded.

Dense retrieval, hybrid rank fusion, contextual chunks and links were considered; none was benchmarked against BM25 here. A fixed-corpus BM25/hybrid comparison is the next proportionate retrieval experiment. [Rationale](../../docs/CODE_MAP.md#retrieval-alternatives-considered)

No new product features are needed to explain this submission. Remaining engineering work is chiefly latency, brevity, API compatibility, broader evidence and reducing supporting infrastructure. The owner should rehearse the tool loop, release checks, memory, trace and evaluation paths before the interview.
