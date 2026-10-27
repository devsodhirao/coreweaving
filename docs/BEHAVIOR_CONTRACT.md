# Permissions, memory and answer release

The assistant answers Weave documentation questions. It can gather evidence and propose examples; it has no account-administration or deployment tool. This contract separates enforced boundaries from fallible model judgments.

## Answer release

1. The planner searches and reads evidence, then proposes a draft. Citation-bearing prose uses the same checks as structured submission.
2. `citation_contract` checks marker syntax, source-ID agreement and whether evidence was read. It does not check truth.
3. `Agent.verify` judges material claims against evidence. Unsupported or partially supported material claims require repair. Default **support** mode does not enforce whole-task completeness; experimental **coverage** adds that check.
4. Rejected drafts receive targeted feedback. Defaults allow 10 planning calls, 18 tool calls and two repairs. On exhaustion, support mode alone can propose up to four supported facts for one additional strict Opus check. A released recovery remains explicitly partial (`kind=insufficient`); unchecked fragments and empty/research-only verdicts cannot release factual answers.
5. The app attempts to save completed answers before rendering and reports save failures. Sources & analysis exposes passages, checks, usage, versions and the trace without another model call. The web app rejects verification-off configuration.

The planner is instructed to answer each requested part, preserve supported content during repair and keep caveats concise. Instructions do not guarantee compliance. [Final answer review](../results/brief-e2e-v1/final-answer-review.json) and [captured code failure](../results/brief-e2e-v1/ui-repair/manual-review.json) show why source checks cannot replace task and code evaluation.

## Permission boundary

| Operation | Enforced scope | Limit |
| --- | --- | --- |
| Search/read | Named tools resolve IDs through the locked local corpus. | No arbitrary URL or host-file access. |
| Python | Non-root Docker; no network, host mounts or credentials; read-only root and fixed resource/time/output limits. | Standard library only; no Weave SDK integration validation or general security guarantee. |
| Dispatch | Exact tool names and arguments are validated in `Agent.execute`. | Prompts and retrieved text cannot add capabilities; topic adherence remains model guidance. |
| Provider/telemetry | Application-configured Anthropic and Weave connections. | These services receive the permitted payload; they are not general network tools for the agent. |
| Credential masking | Configured secrets and recognized key formats are masked before requests, history, traces and saves. | No general PII or unknown-encoding protection. The demo project is public. |

Implementation: [agent.py](../src/coreweaving/agent.py), [sandbox.py](../src/coreweaving/sandbox.py), [config.py](../src/coreweaving/config.py).

## Memory ownership

| Store | Purpose | Lifetime and trust |
| --- | --- | --- |
| `Session.history` | Retain six complete exchanges for follow-ups. | In process; prior answers are not fresh evidence. |
| `Session.evidence` | Preserve original passages and execution receipts behind citations. | Conversation-local and not size-capped; restart loses it. |
| SQLite library | Preserve completed answers and separate dated reviews. | Persistent locally; reviews do not rewrite answers or become documentation authority. |
| Weave | Inspect execution and evaluation records. | Remote records; a conversation ID does not populate model context. |

New conversation resets working dialogue and evidence, not SQLite or remote traces. A UI rerun preserves the background job; process restart can lose it. Promotion from a reviewed failure to a dataset requires manually selecting the question, expected behavior, evidence and visibility. There is no automatic learning or promotion path.

## Behavior contracts and evidence

Given/When/Then checks make the boundaries reproducible. Test names below are in the linked files; scripted-model tests establish control flow, not model reliability.

| Given / when / then | Test or recorded evidence | Scope |
| --- | --- | --- |
| A model requests an unknown tool or extra execution permission → dispatch rejects it. | [test_agent.py](../tests/test_agent.py): `test_unknown_tool_requests_cannot_extend_runtime_permissions`, `test_model_cannot_override_execution_limits` | Capability boundary. |
| A passage includes malicious instructions → it remains tool-result data and cannot grant a tool. | `test_injected_document_instructions_remain_tool_data_and_cannot_grant_a_tool` | No general prompt-injection immunity. |
| A draft contains malformed or unknown citations → checks demand repair before model auditing. | `test_malformed_citation_requires_repair_before_auditor_runs`; [test_evaluate.py](../tests/test_evaluate.py) checks earlier delivered turns too. | Citation identity, not semantic support. |
| A support-mode attempt exhausts its work → any partial recovery must pass a fresh full check. | `test_partial_recovery_requires_its_own_full_check`; [one real recovery replay](../results/recovery-check-v1/receipt.json) | Narrow recovery, not whole-task success. |
| A new conversation starts → old dialogue and citation authority are absent. | `test_fresh_session_inherits_neither_dialogue_nor_citation_authority` | Working context, not deletion of saved records. |
| More than six exchanges finish → retained dialogue stays bounded and original evidence identifiable. | `test_incremental_memory_keeps_six_exchanges_and_original_read_evidence` | No byte cap on the source ledger. |
| A saved answer is reviewed → original evidence remains unchanged. | [test_library.py](../tests/test_library.py): `test_explicit_reviews_keep_history_and_do_not_rewrite_source_check` | Preservation, not truth of the review. |
| The UI navigates while work runs → one job continues and saves before display. | [test_app.py](../tests/test_app.py): `test_pending_work_survives_navigation_and_saves_before_display`; [live navigation check](../results/ui-recovery-v1/browser.json) | No process-crash recovery. |
| A recognized secret enters a request → masking precedes the outgoing and persistence paths. | [test_redaction.py](../tests/test_redaction.py); [live backend canary check](../results/ui-recovery-v1/backend.json) | Recognized formats and inspected sinks only. |

Changes to capabilities, memory or release policy require updated boundary tests and attributable behavioral evidence. [Versioning](VERSIONING.md) explains what each identity covers; version labels themselves grant no permissions.
