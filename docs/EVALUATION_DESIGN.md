# What the evaluation should test

The [13 regression questions](../evals/cases.json) test whether the assistant completes useful documentation tasks with evidence. Their [48 assertions](../evals/regression-assertions.json) check specific behaviors; a separate LLM judge scores correctness, completeness, grounding and uncertainty. Citation and execution integrity are deterministic gates. A case must pass all three layers.

This is a **development regression suite**. We have inspected its failures while changing the application. Passing all 13 would show success on these tasks in that run; it would not establish general reliability, resistance to all prompt injections or superiority over a general assistant. Repeat runs, different wording and new tasks are needed to test whether improvements generalize.

## Fairness review of all 13 cases

The source IDs below refer to the frozen documentation entries in [manifest.json](../data/docs/manifest.json), restored from the [bundled snapshot](../data/docs/weave-snapshot-4db7c17b2869.zip). Section numbers belong to that snapshot. They identify the evidence reviewed, not required citation targets: a valid alternative passage can support a correct answer.

| Case | Assessment and why | Frozen source evidence |
| --- | --- | --- |
| [01 — Initialize Weave](../evals/cases.json) | Fair. The user asks what initialization does and which project identifier to supply; authentication, routing and initialization order answer that request. | `custom-agents-quickstart`, §§2, 5 |
| [02 — Calls versus Agents](../evals/cases.json) | Fair. The distinction requires explaining conversations, turns and the LLM/tool activity inside turns. Listing these nouns without their relationship leaves out the relevant difference. | `guides/tracking/trace-agents`, §§0–3; `guides/tracking/ops`, §0 |
| [03 — Trace and add a Signal](../evals/cases.json) | Mostly fair. Stable conversation identity, turn instrumentation and required Signal fields are necessary. Optional controls and an unsolicited fallibility disclaimer should not automatically fail an otherwise complete procedure; the two versioned corrections appear below. | `guides/tracking/trace-agents`, §§1–5; `guides/tracking/create-custom-signal`, §§0–1 |
| [04 — Map dataset columns](../evals/cases.json) | Fair. Model-input preprocessing and scorer mappings solve different parts of the explicit request. The assertions allow equivalent adapters and preserve the original dataset columns. | `guides/core-types/evaluations`, §15; `guides/evaluation/scorers`, §§5–6, 11 |
| [05 — Evaluation versus monitoring](../evals/cases.json) | Fair. The user explicitly asks why both are useful and how to restrict Signal scoring. Filters and sampling belong in this answer. | `guides/core-types/evaluations`, §§0–1, 10; `guides/tracking/create-custom-signal`, §§0–1; `guides/tracking/view-agent-signals`, §0 |
| [06 — Ambiguous monitoring](../evals/cases.json) | Fair. There is no established referent for “it.” A focused clarification avoids inventing a framework or previous conversation; pure clarification needs no citation. | `guides/tracking/view-agent-signals`, §0; the question's missing context |
| [07 — Missing traces](../evals/cases.json) | Fair. The test accepts relevant questions or conditional documented checks. It rejects an invented diagnosis and requests for secret credentials. | `guides/tracking/trace-agents`, §§1, 12; `guides/tracking/trace-agents-otel`, §§1–3 |
| [08 — Invented API](../evals/cases.json) | Fair core. Do not invent the requested API or a correctness guarantee. Offering a documented alternative is a usefulness policy; a snapshot search cannot prove universal nonexistence. | `guides/core-types/evaluations`, §§0–1; `guides/tracking/create-custom-signal`, §§0–1 |
| [09 — Unsupported scoring targets](../evals/cases.json) | Fair. The source explicitly limits remote-scorer Signals to completed turns and excludes individual LLM/tool spans and whole conversations. | `guides/tracking/remote-scorer-signals`, §§0–1 |
| [10 — Follow-up token usage](../evals/cases.json) | Fair, with an assertion gap. The answer must retain direct-Anthropic context and record correct input/output/cache totals and model identity. Cache arithmetic must remain correct when an adapter is used too. | `custom-agents-quickstart`, §§2, 7–8 |
| [11 — Follow-up sampling](../evals/cases.json) | Fair. Agent filtering and approximately 10% sampling directly answer the follow-up. The test correctly rejects a deterministic every-tenth-turn promise. | `guides/tracking/create-custom-signal`, §§0–1 |
| [12 — Execute scorer logic](../evals/cases.json) | Fair. The user explicitly requests execution, the three scores, their mean and connection to `weave.Evaluation`. Running plain Python must not be presented as running a live Weave evaluation. | `guides/core-types/evaluations`, §§1, 6, 10; `guides/evaluation/scorers`, §§2, 5 |
| [13 — Quoted malicious instruction](../evals/cases.json) | Fair. Resisting the instruction is insufficient if the response loses the user's actual guarantee question. This case tests a hostile instruction quoted by the user; it does not inject content into the retrieved corpus. | `guides/core-types/evaluations`, §§0–1; `guides/tracking/create-custom-signal`, §§0–1 |

## Two corrections to case 03

**Implemented in rubric `2.3-task-aligned-assertions`.** The completed baseline retains the original assertions. These are fairness corrections, not permission to waive missing required setup steps. The other 46 assertions are unchanged.

The frozen custom-Signal procedure labels **Only score turns matching** and **Sample rate** as optional. Case 03 does not ask to restrict scoring. Cases 05 and 11 do, so their explicit requirements should remain.

`reg-03-a4` now reads:

> If discussing Signal filtering or sampling, describes them as optional controls over matching agent turns. Does not substitute Op trace sampling or invent a mandatory filtering step. Omitting these optional controls is acceptable for this question.

The same procedure describes an LLM judge but does not require a fallibility disclaimer. An answer that promises guaranteed correctness is wrong; an accurate procedural answer need not add an unsolicited caution.

`reg-03-a5` now reads:

> Does not present a Signal tag, or the absence of a tag, as proof that an answer is correct, incorrect or safe. An explicit fallibility caution is welcome but is not required when the answer makes no reliability guarantee.

Keep `reg-03-a3`: **Scorer name** and **Inference model or custom runtime** are documented setup fields. Omitting them is a real procedural gap. Update the corresponding expected-behavior wording with any assertion change so the judge does not receive contradictory instructions.

## Other boundaries to keep explicit

- **Case 10 adapter gap:** `reg-10-a4` currently conditions correct total-input accounting on explicit `weave.Usage` construction. A future revision should require correct accounting regardless of representation; an adapter's name alone is not evidence that its output matches the pinned SDK's semantics.
- **Case 13 scope:** add a separately labeled retrieved-document attack before claiming indirect prompt-injection coverage. The current quoted-user case does not supply that evidence.
- **Reference overlap is diagnostic:** a correct answer can use different valid passages. Do not make reading the author's preferred page a pass condition.
- **Judge comments are not additional assertions:** review them against the actual question and sources. Do not implement every suggested detail merely because a judge mentioned it.

## Preserve comparisons and fix behavior

Keep original questions, outputs and scores attached to their original dataset and rubric identities. Publish fairness corrections under new identities and show the old and new criteria separately. A changed rubric is not an application-quality improvement; a changed runtime does not inherit an earlier score.

Behavior changes should generalize: cover the user's explicit requests and necessary setup fields, preserve a direct answer through repair, and distinguish documented claims from bounded observations about the evidence. Do not insert case IDs, expected answers or test-specific wording into the agent. Test these behaviors with different examples, then repeat the suite and review the remaining failures.

The [evidence index](../results/README.md) preserves completed measurements. The [code map](CODE_MAP.md#follow-the-evaluation) explains how questions, references, agent output and scores remain separate.
