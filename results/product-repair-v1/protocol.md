# Product repair validation

This pass repairs defects captured in the [actual Claude chat baseline](../claude-product-baseline-v1/README.md). It keeps production BM25, the snapshot, regression questions, assertions and judge model unchanged.

## Changes under test

1. Preserve valid Python while masking credential literals; reject syntactically invalid Python fences before model auditing.
2. Encode literal reference-like text only on telemetry copies, preserving provider inputs, tool queries and genuine typed Weave references.
3. Plan the requested outcome rather than imposing a full input/trigger/output matrix on every overview. Use explicit medium effort for agent planning and verification; offline judge effort remains at the provider default.

These changes are evaluated as a repair bundle. A difference cannot be attributed to effort alone.

## Frozen checks

- Replay the same six app tasks/seven turns, with exact inputs and criteria copied from the baseline. Fresh conversations except the intentional follow-up; one attempt per turn. No Claude rerun or expanded quality claim.
- Keep the original overview timing criterion and disclose that it exceeds the broad wording. Do not adjust the rubric to improve a score.
- Inspect delivered answers and source support; parse Python fences without executing generated SDK examples. Record visible completion time separately from engine time, cost and model-call count.
- Read actual Weave records back: expected root/model/tool records, provider response IDs and usage. A successful local answer does not establish remote delivery.
- Run the unchanged 13-case `weave.Evaluation` suite once, with a $7 model budget. Preserve completed failures and partial runs. UI turns have a separate $3 observed-cost stop and a 240-second observation limit; these are not provider billing caps.
- Verify Signals with existing filter tests and bounded remote readback; any synthetic export fixture is labeled and separate from answer-quality evidence.

The six-task set and regression are reused development tests. Report failures, static-code limits and delivery gaps. No model bake-off, architectural superiority claim, new rubric, email or change to the original submission tag.
