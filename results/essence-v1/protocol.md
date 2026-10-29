# Simplify around the assignment

Frozen before new model calls. Baseline: 0b2d066, measured runtime dfdb6bd (source 2b4c8d1b6bbf70396fb63a68dcf55361e40bb6fd735fa292c8f803ae8d46c079).

Keep the four-tool conversational loop, exact source/citation validation, Python syntax checks, bounded execution, source/completeness verification, new Weave traces, Signals and unchanged evaluation questions/assertions. Remove the separate task-planning model call, workflow-facet protocol, verifier-owned research, terminal rechecks/quote-based partial synthesis, and SQLite answer-library UI. A partial answer must be authored and checked through the ordinary loop. Keep historical evidence intact.

## Acceptance and measurements

- Local tests must protect citations, tool permissions, truncation, complete dialogue, original-question completeness, rejected-draft isolation and partial-answer labeling. Tests solely for removed features are removed, not rewritten to pretend the feature exists.
- Run the unchanged 13-case regression once on the selected configuration, preserving rubric 2.3. Report failures without altering questions, references or rubric. Review any failures directly.
- Run the same six actual-browser tasks/seven turns and actual overview preset. Target at least the previous 17/18 frozen outcomes and 5/6 tasks, with a lower median visible wait. Also assess literal task fulfillment separately as specified below. The previous seven-turn median is 52.241 seconds; the separate preset is not an eighth benchmark turn.
- Record physical runtime/package line counts before/after separately from moved experiment code. A smaller file alone is not a simpler program; document removed concepts and actual calls.
- Paid validation ceiling: $12 returned-usage estimates across diagnostic, evaluation and UI work; stop for review if that ceiling is threatened. No new model family, retrieval architecture, feature or rubric change in this pass.

## Small matched writer diagnostic

Compare Sonnet and Opus on the SAME frozen candidate source, corpus, medium effort, fixed Opus verifier, tools, limits and caching policy. Preserve the source/config/corpus hashes and exact inputs before the first call. These are reused diagnostics, not held-out model-ranking evidence.

Use these three exact inputs with a fresh session for every attempt:

| Task | Input | Literal fulfillment |
| --- | --- | --- |
| Overview | `product-final-v1/tasks.json`, `01-overview`, first `submitted_text` | Explain the three roles and their relationship with supported claims; do not promise correctness or prevention. Record the old completed-turn timing criterion separately. |
| Direct Anthropic tracing | Same file, `05-anthropic-followup`, first `submitted_text` | Explain appropriate conversation/turn/model/tool instrumentation for the requested Python custom loop. Distinguish tracing identity from model memory. Code is optional; any supplied code must match its stated scope. This diagnostic has no usage follow-up. |
| Ops versus Agents | `evals/cases.json`, `02-calls-vs-agents`, first prompt, with no prefix | Distinguish function Ops from agent conversation/turn semantics and give a supported instrumentation path. Use the three existing `reg-02` assertions as review aids. |

Run **two attempts per task per writer: 12 turns total**, with no regeneration. For round 1, task order is overview, tracing, Ops; within each task use Sonnet/Opus, Opus/Sonnet, Sonnet/Opus respectively. Round 2 uses the same task order with each model pair reversed. Run each pair sequentially, without other paid work concurrently. A pair is the same task and round, not whichever earlier answer looks most comparable.

Keep normal caching enabled for both arms and do not warm only one arm. Record returned cache reads/writes and UTC start times for every call. Show first-round and second-round observations separately when cache state differs; a cold/warm mismatch is a confound, not a model improvement. This does not isolate cold-start latency.

Review outputs against the question and read source evidence, independently of `verified` and runtime completion labels; conceal writer labels during review where practical. Record literal fulfillment, material unsupported claims, citation support and supplied-code defects for each attempt. Syntax validity alone is not API validity or successful execution. A clearly scoped sketch need not be a standalone program. Preserve valid alternate documented answers.

**Selection rule:** prefer Sonnet only if all six of its attempts fulfill their literal tasks, contain no material unsupported claim or code defect, and do not lose a frozen criterion that the paired Opus attempt passes; its total returned-usage cost is lower; and the median of the six paired engine-time ratios `Sonnet / Opus` is at most 0.80, with Sonnet faster in at least four of six pairs. Report each paired time/cost and the ratio, not only a ratio of unrelated medians. The 20% threshold is an engineering adoption margin, not statistical significance. Shared failure or mixed results are inconclusive; retain the current writer without claiming it won. Do not choose using only successful attempts or add trials until a preference appears.

The $12 overall ceiling still applies. If the complete diagnostic cannot fit alongside the final regression and browser replay, stop and mark model selection inconclusive; do not drop an inconvenient pair or replace the planned evidence with a selected subset.

## Quality and denominator rules

- **Useful and complete is the quality target.** A source-supported partial answer can be honestly delivered and still fail the requested task. A justified clarification or correction of a false premise can fulfill its particular request. Do not equate `verified`, `complete`, source count or reference overlap with quality.
- Preserve all 18 browser criteria and their original failures. Criterion `01-overview-a2` requires completed-turn Signal timing that the broad question does not explicitly request. Report the frozen 18-criterion score and a separate literal-task judgment with reasons; do not quietly change the criterion or call omission of that extra detail proof that the literal question was unanswered. A positive claim that Signals block release is a factual defect regardless.
- A browser task passes the frozen rule only if all three criteria pass and no material factual/code defect prevents use. Report all six tasks and seven planned turns, including failures, partials, timeouts and unassessed/unrun items. A fast refusal on an answerable question is not a speed success.
- Regression case pass remains the unchanged formula: every assertion passes, all four judge dimensions are at least 3/4, and deterministic integrity passes. The model's self-verification flag and minimum page count are not pass gates. Report passed cases out of **13 planned**, assertions passed out of **48 planned**, plus graded, ungraded and unrun counts. The existing `assertion_fraction_passed` field divides by valid judged assertions only; label that conditional percentage if shown, rather than presenting it as a full-suite score when judges fail.
- Keep material unsupported claims, unread/unresolvable citations and supplied-code defects visible even if the short checklist passes. Inspect reference scope, API names/arguments, history and cache arithmetic when present. Static inspection is not execution of generated SDK/provider integrations. Trace/export health and cost availability are separate operational checks.

## Timing and interpretation rules

- **Engine time:** measure from entering the complete agent turn to its return, including every research, verification and repair call. Record planner/verifier call counts, retries and costs; exclude the separate offline judge. State whether corpus/init work is outside this interval.
- **Visible time:** measure the browser submission event to the new answer/error being visibly rendered and the turn reaching a terminal UI state. Start at the actual click/Enter event, use monotonic browser time, and verify the observer matches the current UI. Persistence or Weave-export completion alone is not evidence of visible completion. Keep the tab foregrounded and record observation failures.
- Record first answer text separately. Call it **first useful answer** only after inspecting that captured text; the old observer merely classified a nonempty answer block with a non-error runtime kind. Status messages and an unhelpful refusal do not qualify. The final non-streaming answer may have identical first-text and completion times.
- Keep the 240-second timeout. Preserve an error's observed terminal time, and a timeout as right-censored at 240 seconds. Report completion/failure counts beside median/range and all individual times. A completed-only median must disclose exclusions; do not silently discard slow failures or treat a timeout as a fast completed answer. Do not publish a tail percentile from seven observations.
- The seven-turn median weights the two-turn follow-up twice; retain it for historical comparability and list per-task times so that weighting is visible. Keep the separate preset out of this median. Regression timing must distinguish all 15 turns from the 13 final-turn outputs; the old remote mean covered only the latter.
- A historical before/after comparison changes source, provider time and possibly cache state, so it describes observed product performance, not an isolated causal effect. The small paired writer diagnostic controls more of these variables but still cannot establish general superiority. No claim of broad Claude parity or a model ranking follows.

Model comparisons are small and reused; latency depends on provider load. The brief requires useful, explainable behavior and honest evidence, not a universal winner. Existing all-Opus regression 13/13 and browser 17/18 describe the prior source only. Measurement rules above were clarified before new model calls; no historical score or rubric was changed.
