# Historical bounded latency review

This records the investigation before normalization, at commit `7f60a852f2b9e30639e99bc2005adfcd5bb5a0bf`, source SHA-256 `c09d73e4c67c718d7b485608b5e2455b0c8f6648b2c8a93d34be885701d02d80`. Four UI-v2 receipts were joined to 29 backend chat spans by exact response ID. Three conversation queries returned all 74 spans (the overview and follow-up share a conversation). No production source changes were made during that investigation. The proposal was subsequently implemented in final commit `755036e`; its observed results are recorded below.

## Measured time

| UI-v2 turn | Agent.run total | Planner calls/time | Verifier calls/time | Prose-only draft → resubmission |
| --- | ---: | ---: | ---: | --- |
| Overview | 35.74 s | 6 / 19.20 s | 2 / 16.50 s | None |
| Signal follow-up | 28.92 s | 5 / 17.87 s | 1 / 11.02 s | 6.34 s → 3.84 s |
| Python tracing | 49.95 s | 6 / 26.15 s | 2 / 23.76 s | 8.75 s → 5.20 s |
| Evaluation | 40.56 s | 5 / 21.12 s | 2 / 19.41 s | 6.37 s → 5.00 s |

`metrics.MeteredModel.call` measures the whole provider boundary, including SDK, network and tracing work; these are not pure server inference timings. Only 0.025–0.037 seconds per turn remain outside those calls inside Agent.run. This excludes subsequent app persistence, trace flush, polling and rendering. Local search/read parallelism therefore has little demonstrated opportunity in these runs. Caching already returned substantial hits.

Actual backend output proves duplicate drafting in the three named turns: a complete prose-only assistant response, followed by the exact runtime nudge `Use submit_answer to submit your complete draft.`, followed by another planner response containing the draft in submit_answer. The second generation costs 3.84–5.20 seconds in these observations. This identifies avoidable work; it does not guarantee that a changed execution path saves that exact time. The two copies can differ: the Signal follow-up's first prose draft contains an unknown `[C1]` that the submitted copy removes.

Evidence: [UI-v2 timing](ui-v2/latency-summary.json) and [trace readback](ui-v2/latency-trace-readback.json). The historical `agent.py` repeated the planner after prose-only output; `metrics.MeteredModel.call` owns elapsed measurement. The final runtime no longer repeats a cited prose draft merely to obtain tool arguments.

## Rejected prompt experiment

Exactly two fresh-session diagnostic replays appended an explicit tools-only, draft-once instruction in memory. Models, defaults and release checks stayed unchanged; production source remained frozen. One shared model_budget limited estimated spend to $1. No reruns were performed.

| Case | Original → diagnostic time | Diagnostic cost | Prose-only drafts | Audit result |
| --- | ---: | ---: | ---: | --- |
| Python tracing | 49.95 → 25.51 s | $0.1211108 | 1 | Full answer passed; one audit, no recovery |
| Evaluation | 40.56 → 38.66 s | $0.1076617 | 1 | Full answer passed; two audits, no recovery |

Total estimated provider spend: **$0.2287725**. The instruction failed to remove duplicate generation in both prescribed cases, so **do not adopt it**. The tracing speed difference includes one fewer audit and a much shorter verifier response. These are two diagnostic replays, not a benchmark or reliable speedup estimate.

Manual inspection found comparable core guidance: the tracing scaffold retains user and assistant history and labels placeholders; the evaluation answer maps task rows to agent execution and a custom judge, with a documented logger loop. Both the original evaluation answer and diagnostic answer omit explicit judge fallibility, an original UI review criterion; neither receives an unqualified complete-quality pass here. Code was inspected, not executed as part of this diagnostic.

Exact added instruction, original/experimental prompt hashes, settings, all returned blocks, answer receipts and budget accounting are preserved under `tools-only-diagnostic/` (`plan.json`, the two case JSON files and `summary.json`).

## Historical proposal and final result

Normalization is now implemented at commit `755036e`, source `b269258e7786`. A prose-only response with source-like markers enters the existing candidate, verification and release branch. Unknown and malformed markers still fail checked-mode validation; uncited and truncated responses retain their bounded handling. The provider's assistant message stays intact, application origin is recorded, and rejected prose receives ordinary user feedback rather than an orphan tool result. The original proposal preferred checked modes only; the final implementation also normalizes experimental off mode while preserving its explicitly unchecked semantics.

Final UI times were **35.67, 20.85, 22.31 and 32.17 seconds**, respectively. All four answers used provider tool submissions, so those observations cannot establish a normalization speedup. The final regression exercised **four normalized drafts: two accepted and two rejected then repaired**. It completed all 13 cases with **10/13 case passes, 45/48 assertion passes, zero judge errors**, costing an estimated **$2.563052** in returned agent-plus-judge usage. The three failures concern missing nesting detail, omitted Signal setup/caution, and a safe but incomplete recovered answer. Cited prose and source support still do not establish completeness. [Timing comparison](latency-comparison.json) · [Independent evaluation review](evaluation-review.json) · [Final Weave evaluation](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving/weave/calls/01a17bda-f588-7036-abb0-c8139ce36d06)

## Official provider guidance

Anthropic documents that Sonnet 5.5 rejects forced tool_choice `any` and `tool`; explicit prompting is supported but does not force invocation. This matches the observed failure of the prompt-only experiment. [Sonnet 5.5 migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)

Sonnet 5.5 defaults to high effort, and Anthropic suggests starting at medium for well-specified multistep tool workflows and medium/low for latency-sensitive chat. The current request sets no effort. Lowering effort is a separate quality experiment, not evidence of a fix here: measured planner thinking is already modest, while verifier reasoning and revisions account for substantial time. Do not combine effort tuning with submission normalization in the final check. [Effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort)

Anthropic also recommends reducing unnecessary generated tokens and using streaming for perceived responsiveness. Streaming would not shorten the time until this app can release a fully checked answer and would require preserving the existing withholding policy. [Reduce latency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-latency)
