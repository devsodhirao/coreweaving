# Evaluation design

The [13 questions](../evals/cases.json) test useful documentation tasks: setup, multi-page synthesis, ambiguity, follow-ups, execution and false premises. The [48 assertions](../evals/regression-assertions.json) define required outcomes against the frozen [documentation manifest](../data/docs/manifest.json). References go to the offline judge, not the agent.

**Current validation is pending** under the [essence protocol](../results/essence-v1/protocol.md). Verification contract 6 reports audit exceptions instead of supported-claim inventories. Its [writer diagnostic](../results/essence-v1/writer-diagnostic/) used the previous report format and is inconclusive; it cannot establish performance of the current source.

**Historical result: 13/13 cases, 48/48 assertions** on runtime `3a49a50`, rubric `2.3-task-aligned-assertions`. This is a reused development suite: its failures informed repairs. A green run demonstrates those recorded outcomes, not general reliability or superiority over another assistant. The later runtime `dfdb6bd` also reached 13/13 and scored 17/18 frozen browser criteria. Neither result describes contract 6. [Original run](../results/brief-final-regression-v1/summary.json) · [Manual answer audit](../results/brief-e2e-v1/final-answer-review.json) · [Later historical packet](../results/product-final-v1/README.md)

## What each layer measures

| Layer | Question and boundary |
| --- | --- |
| Runtime source verifier | Do read passages support the material claims, and does the answer fulfill the original question in context? Contract 6 returns `passed`, `issues` and `missing_parts`; it has no frozen task plan, workflow facets or positive-claim quotation gate. Citation and Python-syntax checks precede the audit. A passed verdict remains a fallible judgment. |
| Offline LLM judge | Did the answer satisfy the question? Checks per-case assertions and scores correctness, completeness, grounding and uncertainty. Each dimension must reach 3/4, every assertion must pass, and citation/execution integrity must pass for a case to pass. |
| Human review and diagnostics | Inspect actual answers, sources and code, including questionable judge decisions. Reference-page/section overlap diagnoses retrieval; selected references are not exhaustive, and alternate valid evidence is acceptable. |

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

These are selected development controls with AI-authored expected labels, not independent human calibration. Read each reason and its evidence. A malformed or truncated verdict is a delivery failure, not a successful semantic rejection. Fake-model unit tests establish structural handling; real controls test whether the model can use that contract. Final results remain pending.

## Quality, speed and denominators

- **Quality means usefulness for the actual question.** `verified`, source count and runtime completion labels are diagnostics. A supported partial answer can still fail the task. A justified clarification can fulfill its particular task.
- **Keep the planned denominator:** 13 regression cases and 48 assertions, with ungraded, failed and unrun items visible. The existing `assertion_fraction_passed` field divides by valid judged assertions only; label that conditional percentage when grading is incomplete.
- **Keep two browser judgments:** the frozen 18 criteria across six tasks, and literal fulfillment of the prompt with source/code review. The overview's existing timing criterion demands an extra detail not explicitly requested; preserve its score separately. Do not rewrite criteria after seeing results.
- **Engine time** includes every writer, auditor and repair call until the turn returns, excluding the offline judge. **Visible time** runs from browser submission to the answer or error actually appearing. First text counts as useful only after inspecting it; progress text and an unhelpful refusal do not qualify.
- Preserve all seven planned browser-turn timings, errors and 240-second timeouts. Report completion counts with median/range; disclose any exclusions and show the two-turn task separately. The separate preset is outside that median. Regression timing distinguishes 15 total turns from 13 final answers.
- The small writer diagnostic pairs task/repeat, pins auditor and effort, and records cache state. Historical before/after times do not isolate a causal speed gain. A changed source needs fresh validation; shorter audit output alone is not product improvement.

The [protocol](../results/essence-v1/protocol.md) freezes these rules and the bounded selection threshold. Existing saturated regression tasks protect development outcomes; they do not replace harder capability cases or an actual browser replay.

## Are the tasks fair?

These judgments compare the questions with the frozen sources. Required behavior follows the user's request; optional advice is not silently added to the rubric.

| Case | Valid expectation and qualification |
| --- | --- |
| 01 — Initialize Weave | Explain authentication, project routing and initialization order. |
| 02 — Calls versus Agents | Explain the conversation → turn → LLM/tool relationship. Final grading was generous about implicit nesting; the recorded pass remains visible alongside the manual disagreement. |
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

The historical six-task, two-repeat pilot scored off **7/12**, support **10/12**, coverage **8/12**. Off and support tied on **39/44 factual assertions**; support's three extra case passes came from citation integrity. Coverage refused two answerable tasks. The pilot had **no citation-checks-only arm**, so it cannot establish the model auditor's added benefit or justify its latency by itself. [Pilot](../results/coverage-pilot-v1/summary.json) · [Case review](../results/coverage-pilot-v1/review.md)

Selected verifier probes exposed false rejection of deductions and false acceptance of invalid code. Correcting an unfair fixture yielded an old/new tie at **6/6**. That historical policy matched **7/7 selected labels**: six synthetic fixtures and one captured bad tool-history draft. These are development checks, not held-out accuracy estimates. [Fixture correction](../results/brief-e2e-v1/verifier-fixture-review.json) · [Exact final scope](../results/brief-verifier-final-v1/scope-correction.json)

A useful next comparison would hold out new tasks, compare deterministic citations alone with citations plus model verification, and independently review false accepts, false refusals, task completion and latency. That experiment has not been run. Existing outputs and scores remain attached to their original source, dataset and rubric identities. [Evidence index](../results/README.md)

The separate [retrieval probe](../results/retrieval-comparison-v1/README.md) freezes 18 new questions in nine paired families, quoted reference nuggets and six agent tasks before rankings. BM25, source-context BM25 and hybrid share the same result budget and source reads. Hybrid gains 7.4 percentage points of selected-nugget recall, below the predeclared 10-point threshold. References are incomplete relevance judgments; the two-hits-per-page cap also makes full one-search coverage impossible for four questions. Post-hoc checks are labeled separately and do not change selection or grades. The paired live check uses the unchanged judge; independent answer review preserves disagreements with its passes. These results neither replace the regression suite nor measure production reliability.

The later task-completion repair keeps rubric 2.3, its questions and assertions unchanged. Its [separate review](../results/task-completion-repair-v1/review.md) records incomplete measurements, protocol failures, actual app journeys and the distinction between checked facts and a completed task.
