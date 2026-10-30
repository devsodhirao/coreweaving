# Evaluation design

The [13 questions](../evals/cases.json) test useful documentation tasks: setup, multi-page synthesis, ambiguity, follow-ups, execution and false premises. The [48 assertions](../evals/regression-assertions.json) define required outcomes against the frozen [documentation manifest](../data/docs/manifest.json). References go to the offline judge, not the agent.

**Last live-measured runtime:** `a07e5da`, source `b312a2c9a081`, verification contract 6. The [full presentation regression](../results/presentation-regression-retry-v1/README.md) includes the clarification and plain-language changes: 12/13 cases and 47/48 assertions, with every case graded. The uncited clarification alternatives fail. The October 30 [identity check](../results/reviewer-gaps-v1/step-0-identity.json) confirms that the current checkout has the same runtime, dependency lock, questions and grading code. It is not a new quality measurement. Earlier `522c320` results remain historical.

**Historical result: 13/13 cases, 48/48 assertions** on runtime `3a49a50`, rubric `2.3-task-aligned-assertions`. This is a reused development suite: its failures informed repairs. A green run demonstrates those recorded outcomes, not general reliability or superiority over another assistant. The later runtime `dfdb6bd` also reached 13/13 and scored 17/18 frozen browser criteria. Neither result describes contract 6. [Original run](../results/brief-final-regression-v1/summary.json) · [Manual answer audit](../results/brief-e2e-v1/final-answer-review.json) · [Later historical packet](../results/product-final-v1/README.md)

## What each layer measures

| Layer | Question and boundary |
| --- | --- |
| Runtime source verifier | Do read passages support the material claims, and does the answer fulfill the original question in context? Contract 6 returns `passed`, `issues` and `missing_parts`; it has no frozen task plan, workflow facets or positive-claim quotation gate. Citation and Python-syntax checks precede the audit. A passed verdict remains a fallible judgment. |
| Offline LLM judge | Did the answer satisfy the question? Checks per-case assertions and scores correctness, completeness, grounding and uncertainty. Each dimension must reach 3/4, every assertion must pass, and citation/execution integrity must pass for a case to pass. |
| Answer review and AI-assisted diagnostics | Inspect actual answers, sources and code, including questionable judge decisions. Reference-page/section overlap diagnoses retrieval; selected references are not exhaustive, and alternate valid evidence is acceptable. |

`AGENT_MODEL` selects the writer, `VERIFIER_MODEL` the auditor and `JUDGE_MODEL` the offline judge. The provisional configuration uses Opus; the preceding paired diagnostic did not establish a writer winner. There is no runtime recovery judge. Agent calls request medium effort; offline judging retains provider-default effort. Separate calls and reference access give different roles, not independent model families. Shared biases can survive both checks. A source check does not prove SDK compatibility; the sandbox executes plain Python, not generated Weave integrations. [Configuration](../.env.example) · [Evaluation code](../src/coreweaving/evaluate.py)

## Test the checks, not just the answers

A verifier that rejects everything is unusable. Its controls must exercise both acceptance and rejection before a broader regression run. The [five frozen controls](../results/essence-v1/auditor-controls.json) preserve candidate text, source passages, original-record hashes and expected labels:

| Control | Expected behavior and reason |
| --- | --- |
| Corrected recorded Ops draft | Accept supported content; the old positive-quote gate rejected auditor formatting despite all claims being marked supported. |
| Scoped overview synthesis | Accept a relationship composed from documented tracing, evaluation and Signal roles without requiring unrelated legacy alternatives. |
| Invented API with a valid citation | Reject unsupported API existence and a hallucination-free guarantee; citation syntax is insufficient. |
| Two-part question answered in part | Reject a draft labeled complete when an explicitly requested part is missing. |
| Unsupported claim inside a partial answer | Reject the false claim; admitting another omission cannot make it supported. |

These are selected development controls with AI-authored expected labels, not independent human calibration. Read each reason and its evidence. A malformed or truncated verdict is a delivery failure, not a successful semantic rejection. Fake-model unit tests establish structural handling; real controls test whether the model can use that contract. The first compact-audit runtime matched all five selected labels; its semantic review retained incidental overreach in rejection feedback.

Four later [captured-answer controls](../results/essence-v1/scope-controls.json) test operational scope and initialization completeness on `522c320`. Both corrected positives were accepted; one of two negatives was rejected. **The reasons identified neither targeted defect:** the initialization omission was accepted, while the overview was rejected for other, partly debatable reasons that also appear in the accepted positive. Thus 3/4 label agreement is not evidence that those defects were repaired. [Semantic review](../results/essence-v2/auditor-check/semantic-review.json) · [Exact remote delivery](../results/essence-v2/auditor-check/backend-readback.json)

## Quality, speed and denominators

- **Quality means usefulness for the actual question.** `verified`, source count and runtime completion labels are diagnostics. A supported partial answer can still fail the task. A justified clarification can pass an evaluation specifically testing an appropriate next response; it does not complete the user's underlying task. Evaluate the answer after the reply separately.
- **Keep the planned denominator:** 13 regression cases and 48 assertions, with ungraded, failed and unrun items visible. The existing `assertion_fraction_passed` field divides by valid judged assertions only; label that conditional percentage when grading is incomplete.
- **Keep two browser judgments:** the frozen 18 criteria across six tasks, and literal fulfillment of the prompt with source/code review. The overview's existing timing criterion demands an extra detail not explicitly requested; preserve its score separately. Do not rewrite criteria after seeing results.
- **Engine time** includes every writer, auditor and repair call until the turn returns, excluding the offline judge. **Visible time** runs from browser submission to the answer or error actually appearing. The browser observer records terminal prose separately from complete rendering. Version 2 could stop before a code wrapper even appeared; its affected full-render time remains unmeasured. Version 3 continuously captures the DOM until analysis opens, then selects the earliest 250-ms-stable snapshot matching the downloaded answer's prose and code. Missing matches remain unmeasured. [Unpaid instrument controls](../results/essence-v2/observer-v3-proof.json) cover late, empty and multiple code blocks. DOM readiness is not paint or semantic usefulness; progress and an unhelpful refusal do not count as useful answers.
- Preserve all seven planned browser-turn timings, errors and 240-second timeouts. Report completion counts with median/range; disclose any exclusions and show the two-turn task separately. The separate preset is outside that median. Regression timing distinguishes 15 total turns from 13 final answers.
- The small writer diagnostic pairs task/repeat, pins auditor and effort, and records cache state. Historical before/after times do not isolate a causal speed gain. A changed source needs fresh validation; shorter audit output alone is not product improvement.

The [protocol](../results/essence-v1/protocol.md) freezes these rules and the bounded selection threshold. Existing saturated regression tasks protect development outcomes; they do not replace harder capability cases or an actual browser replay.

## Owner decision for the next rubric

On October 30, the owner chose: **“Only fail if the omission prevents completing the user's task; otherwise note it.”** This sets the rule for future grading. A detail can be necessary even when the user does not name it: for example, a required setup step without which the requested workflow cannot work. The reviewer must explain what the omission prevents; appearing in a checklist is not sufficient by itself.

For the multi-turn tracing and Signals example, missing tool-span instructions should be a note unless the user's task needs them. This decision does not excuse incorrect claims, unsupported product advice or missing requested outcomes. It is a grading-policy choice, not a human pass/fail label for any recorded answer.

**Status:** accepted guidance for the next rubric. The running grader, rubric 2.3, its assertions and all recorded scores remain unchanged. Before a new measurement uses this policy, version the judge instructions and affected assertions together. Keep any new grades separate from the existing regression and AI review; do not claim an improvement by rewriting old results.

## Are the tasks fair?

These judgments describe the frozen rubric against the saved sources. Required behavior follows the user's request; optional advice should not be silently added. The owner decision above identifies where the next rubric must make that distinction more explicit.

| Case | Valid expectation and qualification |
| --- | --- |
| 01 — Initialize Weave | Explain authentication, project routing and initialization order. |
| 02 — Calls versus Agents | Explain the conversation → turn → LLM/tool relationship. The historical `3a49a50` review found generous grading of implicit nesting; that pass remains visible alongside the disagreement. The `522c320` retry answers the literal question usefully, but its judge again accepts implicit LLM/tool nesting. [Independent review](../results/essence-v2/regression-resumption-review.json) disputes that assertion pass; the recorded grade stays unchanged. |
| 03 — Trace and add a Signal | Include conversation identity, turn instrumentation and required Signal fields. Two optional demands were corrected below. |
| 04 — Map dataset columns | Address model-input preprocessing and scorer mappings; accept equivalent adapters. |
| 05 — Evaluation versus monitoring | Explain why both help and how to restrict Signal scoring; this question explicitly requests those controls. |
| 06 — Ambiguous monitoring | Clarify the missing referent without inventing context. Pure clarification needs no citation. |
| 07 — Missing traces | Offer relevant questions or conditional checks, not an invented diagnosis or requests for secrets. |
| 08 — Invented API | Reject the invented guarantee and offer documented alternatives. Snapshot search cannot prove universal nonexistence. |
| 09 — Unsupported scoring targets | Explain remote-scorer Signals' documented completed-turn scope. |
| 10 — Follow-up token usage | Retain direct-Anthropic context and correct usage/model accounting. The current assertion only explicitly checks total-input arithmetic for direct `weave.Usage`; adapters leave a rubric gap. |
| 11 — Follow-up sampling | Retain agent filtering and approximately 10% sampling; avoid promising every tenth turn. |
| 12 — Execute scorer logic | Actually run the requested plain-Python calculation and connect it to evaluation without claiming a live Weave run. |
| 13 — Quoted malicious instruction | Resist the quoted instruction and answer the real guarantee question. This is user-message injection, not an attack inserted into retrieved documents. |

## Rubric 2.3: two fairness corrections

The frozen Signal procedure makes filtering and sampling optional. Case 03 asks for setup, not restriction of scoring. It also makes no request for a fallibility lecture. The changed assertions are:

- **`reg-03-a4`:** “If discussing Signal filtering or sampling, describes them as optional controls over matching agent turns. Does not substitute Op trace sampling or invent a mandatory filtering step. Omitting these optional controls is acceptable for this question.”
- **`reg-03-a5`:** “Does not present a Signal tag, or the absence of a tag, as proof that an answer is correct, incorrect or safe. An explicit fallibility caution is welcome but is not required when the answer makes no reliability guarantee.”

Required **Scorer name** and **Inference model or custom runtime** remain in `reg-03-a3`. Cases 05 and 11 still require the filtering/sampling details they request. Questions, references and the other 46 assertions are unchanged.

The fresh baseline scored **10/13, 44/48** under rubric 2.2; the October 27 run scored **13/13, 48/48** under 2.3. Excluding the two changed assertions gives **43/46 → 46/46**. Case 03 already supplied the required setup fields; its improved grade reflects fairness correction. Cases 05/11 delivered previously missing outcomes. Runtime changes occurred together on inspected tasks, so this comparison cannot isolate their causal effects. The tagged submission's separate **10/13, 45/48** result is preserved. [Comparison and versions](../results/brief-e2e-v1/comparison.json)

## What the experiments can tell us

**Example: selected evidence found.** For the screenshot-storage question in the
[offline follow-up](../results/retrieval-followup-v2/README.md), the checklist has
three facts: log a storage URI; configure read access/CORS; register the bucket.
BM25 returns an accepted supporting section for one fact (1/3 = 33.3%); hybrid
returns sections for two (2/3 = 66.7%). The aggregate is the mean of each question's
fraction, so each question has equal weight. This is one search's selected-source
recall, not the probability that an answer is right. Later reads can find missing
facts, and valid unlisted sources can be undercounted by the frozen checklist.

The historical six-task, two-repeat pilot scored off **7/12**, support **10/12**, coverage **8/12**. Off and support tied on **39/44 factual assertions**; support's three extra case passes came from citation integrity. Coverage refused two answerable tasks. The pilot had **no citation-checks-only arm**, so it cannot establish the model auditor's added benefit or justify its latency by itself. [Pilot](../results/coverage-pilot-v1/summary.json) · [Case review](../results/coverage-pilot-v1/review.md)

Selected verifier probes exposed false rejection of deductions and false acceptance of invalid code. Correcting an unfair fixture yielded an old/new tie at **6/6**. That historical policy matched **7/7 selected labels**: six synthetic fixtures and one captured bad tool-history draft. These are development checks, not held-out accuracy estimates. [Fixture correction](../results/brief-e2e-v1/verifier-fixture-review.json) · [Exact final scope](../results/brief-verifier-final-v1/scope-correction.json)

A useful next comparison would hold out new tasks, compare deterministic citations alone with citations plus model verification, and independently review false accepts, false refusals, task completion and latency. That experiment has not been run. Existing outputs and scores remain attached to their original source, dataset and rubric identities. [Evidence index](../results/README.md)

The separate [retrieval probe](../results/retrieval-comparison-v1/README.md) freezes 18 new questions in nine paired families, quoted reference nuggets and six agent tasks before rankings. BM25, source-context BM25 and hybrid share the same result budget and source reads. Hybrid gains 7.4 percentage points of selected-nugget recall, below the predeclared 10-point threshold. References are incomplete relevance judgments; the two-hits-per-page cap also makes full one-search coverage impossible for four questions. Post-hoc checks are labeled separately and do not change selection or grades. The paired live check uses the unchanged judge; independent answer review preserves disagreements with its passes. These results neither replace the regression suite nor measure production reliability.

The live subset excluded the three questions with offline hybrid gains. The [follow-up](../results/retrieval-followup-v2/README.md) therefore tests fresh wording of selected gain/loss tasks and exact-API controls on current retrieval, without model calls. It separately reports selected sections, reachable reference pages and exact quotes exposed if the hits were read. The new wordings are development diagnostics, not independent information needs. Neither the old adoption threshold nor the new offline gain establishes final-answer quality; that needs repeated paired agent runs and source-based answer review.

The later task-completion repair keeps rubric 2.3, its questions and assertions unchanged. Its [separate review](../results/task-completion-repair-v1/review.md) records incomplete measurements, protocol failures, actual app journeys and the distinction between checked facts and a completed task.
