# Claude product baseline v1 — frozen protocol

This is a first-attempt comparison of the current Coreweaving web app and regular Claude desktop chat on six existing user tasks (seven submissions per product). It measures the product experience, not a controlled comparison of models or retrieval architecture. This file and [tasks.json](tasks.json) are frozen before either product answers; they contain no results.

## Products and input

- **Coreweaving:** actual web UI, production BM25, support verification, runtime `fe4b7b5ea5fe1b661945a7129cc9d8a29f6565ba`, source SHA-256 `860e9ee6c1134ca44ed04ac9dd22103e2c8acfe5f64fe40a0969941034af53ff`, October 24 documentation snapshot `4db7c17b28698bcc2680da22d687f7c4783ecf5e5255e16177b9197e56da14b4`. Expected planner/ordinary verifier: Sonnet 5.5; existing terminal judge: Opus 5.5. Preserve normal bounded internal research, verification and retry behavior.
- **Claude:** regular desktop chat, currently reported UI labels **Opus 5.5 / Extra / Auto**, with ordinary available tools/settings. Use a fresh incognito chat for each independent task, with no Project or attachments; retain that same incognito chat for the follow-up pair. Native web access is available as normal; record actual use and the labels/tool availability observed. Do not change global settings. Do not substitute Claude Code, an API call, or an imitation of the chat product. Subscription cost is unknown.
- The exact documentation entry is `https://docs.wandb.ai/weave`. The operator observed this URL redirecting to the official `https://docs.coreweave.com/products/wandb/weave`; retain the original URL in the frozen prefix and record any access failure without silently replacing the input. A URL change before any answer requires a new freeze of both files.

Every fresh first turn in BOTH products uses this exact prefix, including two trailing newlines, followed by the frozen question:

```text
Use the Weave documentation at https://docs.wandb.ai/weave to answer this question:

```

The follow-up receives no URL prefix. `tasks.json` stores complete submitted strings; use those bytes rather than reconstructing prompts. Do not supply reference answers, rubric text, source IDs, retrieved passages, or additional instructions to either product. Fresh app conversations and fresh Claude incognito chats for independent tasks; keep the two follow-up turns together, using each product's own preceding answer and history. Do not paste one product's answer into the other.

## Order and limits

Run tasks in their listed order in tasks.json. Alternate app-first and Claude-first by list position. On task 05, complete both turns in one product before starting the other product's fresh conversation. Before any answers, the known URI export-failure task (02) was placed last so a shared exporter failure cannot contaminate later tasks; no question or criterion changed. This is an explicit execution-order choice, not a claim that the app can recover from that failure.

Maximum: seven submitted turns per product, one attempt at each planned turn. No operator regeneration, rewritten questions, corrective follow-ups, or selective reruns. Existing internal app calls remain part of that one attempt and should be reported; Claude's internal work may be unobservable. A clarification request is retained as the answer, without inventing an additional user turn.

Allow 240 seconds per submitted turn for visible completion. Preserve timeout, refusal, error and partial output as observed; do not wait past the deadline and relabel the result as on time. If a timed-out first turn prevents the planned follow-up, record the follow-up as not run with its dependency reason rather than creating a replacement conversation. Stop starting app turns when observed cumulative app cost reaches $5; this is an observation-based stop, not a hard billing cap. An in-flight turn or delayed usage can exceed it. Record unrun tasks and unknown costs. No paid LLM judge calls are part of this comparison.

## Shared grading

Use the three frozen outcomes per task in `tasks.json` (18 total), then manually review sources, unsupported claims, and code on BOTH products. Record each outcome as pass/fail/unassessed with answer and evidence locations. Report outcome counts and full-task completion separately; a full task requires all three outcomes and no material factual or code defect that prevents the requested use. Retain unassessed and unrun counts explicitly; do not silently drop them from the six-task denominator. Do not award a complete-task pass for a correct but incomplete refusal or partial answer.

Accept Claude's native citations, ordinary source URLs, and the app's resolvable source markers equally. Check that material product claims have attributable supporting documentation, links resolve to relevant evidence, and the evidence actually supports their scope. Neither S# syntax nor app-only read-ledger, verifier, task-plan, or execution-receipt conventions are required of Claude. References are review aids, not exhaustive answer templates; alternate documented solutions are valid. Optional advice becomes reviewable when supplied but does not create extra required outcomes.

For code, inspect actual API names, argument mappings, conversation history, token arithmetic, imports and placeholders. A clearly labeled sketch need not be a standalone program. Code is optional for the paraphrase task; any supplied code is still judged for correctness. Do not infer executable validity merely from a documentation citation. No generated code execution or remote integration test is included here; mark those checks unperformed. No reliability guarantee follows from an app verifier pass or a judge-like statement in either answer.

## Timing and records

For every turn, preserve the exact input, delivered output, visible model/settings, browsing/tool observations, available citations, status and timestamps. Measure submit-to-first-useful-answer-text and submit-to-final-visible-completion separately when observable. Progress messages, search activity and generic status text are not useful answer text. If an endpoint cannot be observed reliably, mark that metric unmeasured rather than estimating it. Record timeout latency as censored at 240 seconds. Report paired task results, medians/ranges with counts, and failures; a completed-only latency statistic must disclose exclusions.

App engine elapsed time excludes persistence/export/rendering and is secondary to the UI measure. Do not compare it directly with Claude's visible wait or with older runtime/task baselines. Report app usage estimates separately from the unknown subscription allocation; do not describe Claude as free or claim a cost winner.

The exact-API task contains `weave:///`. Prior ordinary query literals beginning with that prefix caused trace-export rejection. Record export delivery separately from visible answer quality; do not sanitize the task, retrieval queries, or answer to conceal that risk. The comparison requires no tracing contract from Claude.

## Interpretation limits

These are reused development questions, not held-out tasks or a general reliability estimate. Claude's live web access and model/settings differ from the app's frozen snapshot and model mix. Record documentation dates and version-sensitive disagreements; verify claimed APIs against appropriate official evidence without treating a newer documented API as false merely because it is absent from the snapshot. Neither a controlled architectural advantage nor a general product ranking follows from six tasks. Preserve disagreements between outcome grades, source review, code review, export status and visible usability.
