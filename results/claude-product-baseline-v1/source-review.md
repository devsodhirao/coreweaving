# Source notes for the frozen product comparison

Prepared from official documentation and the local snapshot on 2026-10-29 UTC, before reviewing this comparison's answers. This is a grading reference, not an amended rubric or an answer-quality result. No model requests or remote integration tests were made.

Frozen inputs:

- Protocol: `results/claude-product-baseline-v1/protocol.md`, SHA-256 `c2336d773f0da02b04e179fb2ca059d2bbb5efc01cad1007b8d72fb2fd7bcefc`.
- Tasks: `results/claude-product-baseline-v1/tasks.json`, SHA-256 `c28012b90ee731632ad639b5cdd2845db56ed70330bcb90c5c6687d164844cf7`.
- App corpus: 2026-10-24 snapshot `4db7c17b28698bcc2680da22d687f7c4783ecf5e5255e16177b9197e56da14b4`.
- Installed Python Weave: `0.54.0`. The manifest's `0.53.1` label describes its reference-page source; it does not establish compatibility of every guide.

## Sources and short excerpts

Section numbers below are zero-based `Corpus.read(page_id, section)` coordinates, not website heading numbers. The cited current pages and snapshot agree on the material contracts below. URLs use the current canonical host; the task's `docs.wandb.ai/weave` entry redirects there.

| Key | Official source and snapshot coordinates | Short excerpt / supported point |
| --- | --- | --- |
| REF | [Store and track versions of prompts](https://docs.coreweave.com/products/wandb/weave/guides/core-types/prompts-version), `guides/core-types/prompts-version` §§3–4 | “Does not require calling `weave.init(...)`.” This applies to fully qualified refs; the two shorthand forms explicitly require initialization. |
| OP | [Customize Ops](https://docs.coreweave.com/products/wandb/weave/guides/tracking/ops), `guides/tracking/ops` §3 | “without modifying the original function”; the documented hooks alter the logged representation. |
| TRACE | [Trace your agents](https://docs.coreweave.com/products/wandb/weave/guides/tracking/trace-agents), `guides/tracking/trace-agents` §§2–7 | “A conversation groups turns by a shared `conversation_id` attribute rather than a parent span”. |
| USAGE | [Custom agent observability quickstart](https://docs.coreweave.com/products/wandb/weave/custom-agents-quickstart), `custom-agents-quickstart` §§5,7–8 | “`input_tokens` is the total input, including any cached tokens.” The Anthropic example adds both cache buckets to its provider input count. |
| SIGNAL | [Score agent turns with a remote scorer](https://docs.coreweave.com/products/wandb/weave/guides/tracking/remote-scorer-signals), `guides/tracking/remote-scorer-signals` §1 | “Weave scores only completed turns.” Root-span completion triggers `weave.genai.turn_ended`, then filtering/scoring and feedback. |
| SIGNAL-UI | [Monitor your agents with signals](https://docs.coreweave.com/products/wandb/weave/guides/tracking/view-agent-signals), `guides/tracking/view-agent-signals` §§0,3–5 | “Only `turn` is supported.” Signals provide tags/ratings and surface quality or safety issues; they do not promise prevention. |
| EVAL | [Evaluations overview](https://docs.coreweave.com/products/wandb/weave/guides/core-types/evaluations), `guides/core-types/evaluations` §§5–10,15,18 | “Scorer functions always receive the original dataset example, without any preprocessing applied.” |
| SCORE | [Scoring overview](https://docs.coreweave.com/products/wandb/weave/guides/evaluation/scorers), `guides/evaluation/scorers` §§5–6,8–9 | “`{scorer_keyword_argument: dataset_column_name}`” is the Python class-scorer mapping direction. |

## The 18 frozen criteria

These are explanations of existing criteria. Do not turn optional implementation details below into new requirements.

| Criterion | Source-grounded review boundary |
| --- | --- |
| `01-overview-a1` | TRACE/EVAL/SIGNAL-UI: execution records for diagnosis; repeatable dataset runs with scores for comparison; ongoing turn scoring for monitoring. A useful connection is production findings becoming evaluation examples, followed by inspecting traces to explain failures. No mandated wording or diagram. |
| `01-overview-a2` | SIGNAL: completion precedes scoring. Saying only “online” or “real time” does not establish this timing. An application may separately implement an inline check; Signals must not be described as that answer-release mechanism. |
| `01-overview-a3` | SIGNAL-UI describes detection and review, not proof of safety or correctness. Ordinary monitoring language is acceptable; no unsolicited safety lecture is required. |
| `03-paraphrase-a1` | OP: `postprocess_inputs` and `postprocess_output` are appropriate decorator options for the stated Python need. A global redaction approach alone must still satisfy both requested input and output behavior. |
| `03-paraphrase-a2` | OP: input callback receives argument-name/value dictionary and returns a transformed dictionary; output callback receives the ordinary return value and returns its logged representation. Do not confuse these with modifying arguments before business execution. |
| `03-paraphrase-a3` | OP: omit/mask selected fields in copies or newly constructed representations. Review supplied code for actual preservation of function inputs/return behavior, especially mutations of nested objects. Code is optional, but syntactically broken or behavior-changing supplied code is a real defect. |
| `04-evaluation-workflow-a1` | EVAL/SCORE: dataset names match prediction parameters; prediction result becomes scorer `output`; other scorer arguments receive relevant row fields such as references. Explain any renaming consistently. `preprocess_model_input` changes model inputs only. |
| `04-evaluation-workflow-a2` | EVAL: dataset/list, an instrumented function or Model, scorers, then `await evaluation.evaluate(model_or_function)` (or `asyncio.run` in synchronous code). Equivalent documented procedures, including EvaluationLogger, qualify. Pass the callable, not its already computed return value. |
| `04-evaluation-workflow-a3` | SCORE: a judge assesses criteria relevant to the user's agent and returns reviewable metrics/reasons. Inputs must include the material needed for the stated rubric. Explanations of recorded per-row results and/or aggregate review qualify; a lecture on judge fallibility is not required. |
| `05-anthropic-followup-a1` | TRACE: group turns by conversation identity; instrument each exchange, provider request, and tool execution. End spans with context managers/finally. Preserve direct Anthropic/Python context. Conversation identity does not populate the provider's message history. |
| `05-anthropic-followup-a2` | USAGE: place usage and priceable model identity on the model/chat span. Account for input, output, cache read, and cache creation. Direct `Usage` construction or a suitable adapter is valid; an unexplained OpenAI-only response shape is not. |
| `05-anthropic-followup-a3` | USAGE plus adapter note below: add Anthropic's disjoint cache counts exactly once to Weave input total, while retaining both cache categories. Preserve preceding assistant responses/tool-use blocks if supplying loop code. Dollar figures require actual usage/pricing evidence. |
| `06-false-premise-a1` | The literal requested API has zero occurrences in the 351-page snapshot and is absent from installed Weave's public attribute namespace. That supports a bounded “not a documented/supported API here,” not a universal claim about every future version. |
| `06-false-premise-a2` | Reject the never-hallucinate guarantee; do not merely replace the fake call with another purported guarantee. |
| `06-false-premise-a3` | TRACE/EVAL/SIGNAL-UI support tracing, evaluation and monitoring alternatives. Documented application guardrails may also qualify. They need not be a particular class or this app's custom verifier. |
| `02-exact-api-a1` | REF: `support_prompt:v3` selects version index v3; bare `support_prompt` resolves latest. Hashes/aliases are also supported selectors. An alias can move; an immutable stored version's contents do not. |
| `02-exact-api-a2` | REF: `weave.ref(...)` constructs the reference; `.get()` fetches its object. Returning a URI/reference alone is not the same action. |
| `02-exact-api-a3` | REF: shorthand refs need the initialized project context; `weave:///entity/project/object/support_prompt:v3` supplies that identity and does not require `weave.init`. This does not imply public access, no authentication, or no network request. |

## Version and code-review cautions

**Anthropic adapter, inspected locally rather than inferred from its name.** In installed Weave 0.54.0, the import is `from weave.conversation.adapters.anthropic import usage_from_anthropic`. It accepts the complete Anthropic response Message, accesses `message.usage`, copies raw `input_tokens` unchanged, and copies nullable cache fields as zero when absent. Calling it with only `response.usage` is incorrect for this version. The helper is not exported as `weave.usage_from_anthropic` or `weave.conversation.usage_from_anthropic` here. An adapter-only answer is insufficient if it claims cache-inclusive totals without adjustment. Do not prescribe adding caches again if evidence shows a different adapter version already normalizes them.

For example, raw counts 10 ordinary input + 20 cache-read + 30 cache-creation require Weave input 60, read 20, creation 30; output remains the provider's output count. Weave derives price from usage/model identity, preferring `response_model`; a missing price table entry still prevents a cost display. Recording tokens is not proof of exact billing. These are cache/accounting checks, not a requirement to supply code.

**Custom loop provenance.** Agent and conversation are grouping concepts, not extra root spans. Each turn has its own trace. The application retains message history separately. For Anthropic, keep the assistant's content (including `tool_use`) before the corresponding user `tool_result` message, and retain final assistant responses across turns. The Weave trace representation need not be passed back as provider history. A short instrumentation sketch need not implement a complete agent; assess the completeness it claims.

**Source examples are evidence, not executable guarantees.** The current EVAL full-code section includes a misleading call that evaluates a function's return value. Its dedicated function section correctly passes the function itself. Grade actual supplied code using the documented API contract rather than granting correctness because a snippet was copied. Similarly, the quickstart's main loop uses OpenAI; its separate Anthropic usage example supplies the relevant cache conversion. Do not silently apply OpenAI message fields to Anthropic.

**Absence and freshness bounds.** Current official Python-reference fetch failed through the browsing tool; no claim of an exhaustive current-web API absence audit is made. The other eight official pages were accessible. A newer supported API shown by a product's credible source remains eligible even if missing from the snapshot. Signals' completed-turn evidence is explicit for agent-turn scoring; legacy Op/Call monitors are a separate surface.

**Shared grading fairness.** Accept native citations, URLs, or resolvable source markers equally. No requirement for this app's read ledger, task-plan facets, verifier badges or local snapshot. Record material unsupported advice separately. Keep answer quality separate from trace export, token telemetry and visible-completion failures. The six tasks remain 18 criteria even when an operational failure makes some unassessed. No outputs have been graded in this note.
