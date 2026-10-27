# Evaluation design

The [13 questions](../evals/cases.json) test useful documentation tasks: setup, multi-page synthesis, ambiguity, follow-ups, execution and false premises. The [48 assertions](../evals/regression-assertions.json) define required outcomes against the frozen [documentation manifest](../data/docs/manifest.json). References go to the offline judge, not the agent.

**Current result: 13/13 cases, 48/48 assertions** on runtime `3a49a50`, rubric `2.3-task-aligned-assertions`. This is a reused development suite: its failures informed repairs. A green run demonstrates those recorded outcomes, not general reliability or superiority over another assistant. [Run](../results/brief-final-regression-v1/summary.json) · [Manual answer audit](../results/brief-e2e-v1/final-answer-review.json)

## What each layer measures

| Layer | Question and boundary |
| --- | --- |
| Runtime source verifier | Do the passages actually read support the answer's material claims? Support mode checks claims made, not complete task coverage. Deterministic citation checks precede the model audit. |
| Offline LLM judge | Did the answer satisfy the question? Checks per-case assertions and scores correctness, completeness, grounding and uncertainty. Each dimension must reach 3/4, every assertion must pass, and citation/execution integrity must pass for a case to pass. |
| Human review and diagnostics | Inspect actual answers, sources and code, including questionable judge decisions. Reference-page/section overlap diagnoses retrieval; selected references are not exhaustive, and alternate valid evidence is acceptable. |

The planner and support verifier use Sonnet; the offline judge and recovery check use Opus. Separate calls and reference access give different roles, not independent model families. Shared biases can survive both checks. A source check does not prove SDK compatibility; the sandbox executes plain Python, not generated Weave integrations. [Evaluation code](../src/coreweaving/evaluate.py)

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

The fresh baseline scored **10/13, 44/48** under rubric 2.2; the final run scored **13/13, 48/48** under 2.3. Excluding the two changed assertions gives **43/46 → 46/46**. Case 03 already supplied the required setup fields; its improved grade reflects fairness correction. Cases 05/11 delivered previously missing outcomes. Runtime changes occurred together on inspected tasks, so this comparison cannot isolate their causal effects. The tagged submission's separate **10/13, 45/48** result is preserved. [Comparison and versions](../results/brief-e2e-v1/comparison.json)

## What the experiments can tell us

The historical six-task, two-repeat pilot scored off **7/12**, support **10/12**, coverage **8/12**. Off and support tied on **39/44 factual assertions**; support's three extra case passes came from citation integrity. Coverage refused two answerable tasks. The pilot had **no citation-checks-only arm**, so it cannot establish the model auditor's added benefit or justify its latency by itself. [Pilot](../results/coverage-pilot-v1/summary.json) · [Case review](../results/coverage-pilot-v1/review.md)

Selected verifier probes exposed false rejection of deductions and false acceptance of invalid code. Correcting an unfair fixture yielded an old/new tie at **6/6**. The final policy matched **7/7 selected labels**: six synthetic fixtures and one captured bad tool-history draft. These are development checks, not held-out accuracy estimates. [Fixture correction](../results/brief-e2e-v1/verifier-fixture-review.json) · [Exact final scope](../results/brief-verifier-final-v1/scope-correction.json)

A useful next comparison would hold out new tasks, compare deterministic citations alone with citations plus model verification, and independently review false accepts, false refusals, task completion and latency. That experiment has not been run. Existing outputs and scores remain attached to their original source, dataset and rubric identities. [Evidence index](../results/README.md)
