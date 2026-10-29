# Actual Claude chat comparison

**Ordinary Claude can answer these documentation questions. This comparison gives us no demonstrated answer-quality advantage.** The clearest app defect is malformed Python that passed verification; the clearest operational defect is missing trace delivery for a literal reference-URI query. Both are repair targets, not reasons to add another retrieval system.

The [protocol](protocol.md) and [six tasks](tasks.json) were committed as `09b177f` before any answers. Each product received seven submissions, including one two-turn conversation. Questions included the same documentation URL; no answer was regenerated. Runtime remained `fe4b7b5` / source `860e9ee6c113` throughout.

## What was compared

| Product | Model and settings | Documentation and memory |
| --- | --- | --- |
| Actual Coreweaving web UI | Sonnet 5.5 planner/verifier; configured Opus recovery; API effort unspecified | Production BM25 over the October 24 snapshot; fresh task conversations, shared history for the follow-up |
| Actual regular Claude desktop chat | **Opus 5.5 · Extra effort · Auto** | Native web tools and the supplied URL; incognito chats, shared history for the follow-up |

This tests whole products with different models, effort and access paths. It does not isolate retrieval. Incognito suppresses saved memory: a new conversation is still the same person, but this experiment isolates task history rather than testing personalized Claude. Coreweaving currently has conversation history, not a persistent user-profile system.

## Answers

Codex inspected the supplied code and checked claims against official sources. This is AI-assisted review, not human-calibrated ground truth. Python parsing and SDK inspection were static; generated examples were not executed.

| Task | Coreweaving outcomes | Claude outcomes | What the review found |
| --- | ---: | ---: | --- |
| Explain tracing, evaluations and Signals | 2/3 | 2/3 | Both useful overviews; neither fully states the frozen completed-turn timing criterion. |
| Hide private input/output fields | 2/3 | 3/3 | App masking damages the Python signature and return statement. Claude supplies valid illustrative code. **Session deviation: excluded from the clean comparison.** |
| Dataset + LLM judge workflow | 3/3 | 3/3 | Both provide a usable documented procedure; explicit placeholders remain. |
| Anthropic tracing + usage follow-up | 3/3 | 3/3 | Both retain context, preserve history and give correct cache arithmetic. Minor integration caveats remain. |
| Invented hallucination-free API | 3/3 | 3/3 | Both reject the API/guarantee and give documented alternatives. |
| Exact prompt reference/version API | 3/3 | 3/3 | Both explain version selection, retrieval and initialization correctly. App telemetry is incomplete. |

On the **five clean task pairs**, both meet **14/15 outcomes and all criteria on 4/5 tasks**. Keeping every observed answer yields 16/18 versus 17/18, but the privacy pair had inherited Claude history and cannot establish a controlled advantage. No cases are silently dropped: all six remain in [summary.json](summary.json), with exclusions explicit.

The overview timing criterion goes beyond the literal broad question. Its omission makes the checklist incomplete; it does not make either overview useless. We retained the frozen grades and this instrument limitation rather than changing the rubric after seeing the answers. Detailed reviews: [overview](reviews/review-overview.json), [privacy](reviews/review-paraphrase.json), [evaluation](reviews/review-evaluation.json), [follow-up](reviews/review-followup.json), [false premise](reviews/review-false-premise.json), [references](reviews/review-exact-api.json).

## Waiting and cost

| Turn | App final visible | Claude final observed |
| --- | ---: | ---: |
| Evaluation workflow | 30.2 s | 69.0 s |
| Anthropic setup | 57.2 s | 58.3 s |
| Usage follow-up | 29.3 s | 49.2 s |
| Invented API | 40.2 s | 44.0 s |
| Exact references | 22.2 s | 23.9 s |
| **Median of these five turns / four tasks** | **30.2 s** | **49.2 s** |

These are observed product waits, not model-speed estimates. Claude streamed useful text before completion; the app withheld its answer until checks finished. Sampled first-useful-text bounds and observation gaps are in [timing-review.json](timing-review.json). Claude's native read-only web approvals are included. The overview has an operator/permission delay and an app completion-observer error, so it is excluded from the speed summary; the privacy pair is also excluded. Both original receipts remain available.

App calls cost an estimated **$1.22 across 47 model requests** using returned usage and dated prices. Claude's subscription allocation is unknown. No paid judge API calls were made. This does not establish a cost winner or general latency ranking.

## Trace delivery and repairs

[Backend readback](backend-readback.json) finds **6/7 Agent roots, 43/47 model records, and 42/47 fully linked and usage-reconciled requests**. The exact-reference task displayed its answer but issued `weave:/// URI ref weave.init required`; its root and four model records are absent. The earlier [offline converter reproduction](../retrieval-comparison-v1/export-reproduction/probe.py) explains the literal-text/reference confusion. Successful UI delivery does not repair that export defect.

The next implementation pass is limited to:

1. Preserve Python structure while masking actual credentials; validate delivered code rather than relying on source support alone.
2. Keep literal text distinct from typed Weave references at serialization, without changing what the agent searches or reads.
3. Check requested outcomes concisely, keep verification effort explicit, and measure quality and waiting on the unchanged questions.

The 57%/64% retrieval figures in the [earlier experiment](../retrieval-comparison-v1/README.md) measure required facts in six results from a single query. They are not these answer-quality scores. Our agent already performs multiple searches and reads; changing the ranker would not fix either demonstrated defect above.

## Reproduction and deviations

Use the exact inputs, task order and limits in [tasks.json](tasks.json). The ordinary Claude chat baseline is a real UI run, not Claude Code or an API imitation. [Source notes](source-review.md) give the grading references; [artifact-map.json](artifact-map.json) maps private working paths in review receipts to their public copies. Raw app results/statuses and Claude accessibility captures preserve delivered output.

- The first app observer missed an icon-prefixed completion button. Full answer text was observed at 105.4 s; completion was manually confirmed by 162.7 s. The correction is explicit in its receipt.
- The first Claude observer mistook a web permission request for completion. The same original turn continued after approval; its 133.3 s includes the operator delay. It was not resubmitted.
- The desktop New Chat action initially left the incognito conversation open. The privacy question inherited overview history. Subsequent independent tasks explicitly exited incognito and asserted that no previous user messages remained.
- Models, effort, snapshot/live access, reused development tasks, small sample, unexecuted generated code and AI-assisted grading limit generalization. Neither a product superiority claim nor an architectural win follows from this run.
