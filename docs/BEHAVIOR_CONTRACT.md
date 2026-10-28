# Permissions, memory and answer release

The assistant answers Weave documentation questions. It can gather evidence and propose examples; it has no account-administration or deployment tool. This contract separates enforced boundaries from fallible model judgments.

## Answer release

1. `Agent.plan_task` derives requested outcomes from the question and retained dialogue before retrieval. Focused tasks use up to six ordinary outcomes. Broad workflow comparisons name up to six subjects; Python expands each into separate input, execution-trigger and output outcomes. Each quotes a user request; Python assigns fixed IDs. This call consumes one of the ten planning calls. Outcome selection is a model judgment, not a proof that every user intent was captured.
2. The planner searches and reads evidence, then proposes a draft. Citation contract version 3 parses CommonMark using the UI's dedent/strip normalization. Every visible ID must be read and declared; links, definitions and encoded markers cannot impersonate citations. This checks identity, not truth.
3. Verification contract version 3 checks claim support **and each fixed question outcome** in both enabled modes. Python requires the exact outcome-ID set and exact candidate quotes; deleting a requested part or changing answer kind cannot clear it. Answered workflow facets additionally require literal quotations from read, cited evidence. Enabling a workflow does not establish the event that triggers each execution. Product claims also require an applicability judgment. Integration documentation can support a shared API it actually describes; unrelated integration behavior cannot automatically become a general API claim.
4. Missing evidence can produce at most two typed research requests per verdict. The runtime executes eligible searches or reads through the existing dispatch and eighteen-research-dispatch budget, then returns the observations to the planner. Reads must name navigation supplied to the verifier. Linked pages and search hits are navigation, never citation authority. Optional unsupported extras can be removed or narrowed.
5. Experimental **support+coverage** additionally checks source-derived caveats. Default **support** checks the requested task without importing every caveat from retrieved pages. Two repair rounds remain the default. Research exhaustion does not block submissions using existing evidence; the last planning call offers submission only. On exhaustion, support mode has one terminal `JUDGE_MODEL` check. It can strictly recheck a complete draft when a positive auditor judgment failed record/provenance checks, or check up to four supported facts as a partial answer. Eligibility is application-owned; the full path checks every outcome and has no second fallback. Unresolved task outcomes stay structured and visible beside a partial answer; they are never appended to audited prose after validation.
6. A truncated planner response never enters conversation history or executes tools. One fresh retry can consume the next existing planning slot with a 4,800-token allowance; normal calls use 2,400. A second truncation or final-slot truncation stops explicitly. A completed retry must still pass the ordinary citation, support and task checks.
6. The app attempts to save completed answers before rendering and reports save failures. Sources & analysis exposes the task plan, sources, checks, usage, versions and trace without another model call. The web app rejects verification-off configuration.

Semantic support, applicability and fulfillment remain fallible model judgments. The runtime enforces the contract around those judgments; it does not independently prove them. Historical source-only support results belong to verification contract version 1 and cannot establish the new task-completion policy's benefit.

## Permission boundary

| Operation | Enforced scope | Limit |
| --- | --- | --- |
| Search/read | Named tools resolve IDs through the locked local corpus. | No arbitrary URL or host-file access. |
| Python | Non-root Docker; no network, host mounts or credentials; read-only root and fixed resource/time/output limits. | Standard library only; no Weave SDK integration validation or general security guarantee. |
| Dispatch | Exact tool names and arguments are validated in `Agent.execute`. | Prompts and retrieved text cannot add capabilities; topic adherence remains model guidance. |
| Provider/telemetry | Application-configured Anthropic and Weave connections. | These services receive the permitted payload; they are not general network tools for the agent. |
| Credential masking | Configured secrets and recognized key formats, quoted assignments and Basic/Bearer authorization values are masked before requests, history, traces and saves. An unclosed quoted assignment is masked through line end. | No general PII or unknown-encoding protection; explicit placeholders remain readable. The demo project is public. |
| Chat rendering | Parsed Markdown images become escaped alt text; raw HTML and JavaScript are disabled in that rendering path. Code and ordinary links remain usable. | This prevents automatic chat-image loading, not intentional navigation through a link or all browser networking. |

Implementation: [agent.py](../src/coreweaving/agent.py), [sandbox.py](../src/coreweaving/sandbox.py), [config.py](../src/coreweaving/config.py).

## Memory ownership

| Store | Purpose | Lifetime and trust |
| --- | --- | --- |
| `Session.history` | Retain six complete exchanges for follow-ups. | In process; prior answers are not fresh evidence. |
| `Session.evidence` | Preserve original passages and execution receipts behind citations. | Conversation-local and not size-capped; restart loses it. |
| SQLite library | Preserve completed answers and separate dated reviews; serialize concurrent review appends in a transaction. | Persistent locally; reviews do not rewrite answers or become documentation authority. |
| Weave | Inspect execution and evaluation records. | Remote records; a conversation ID does not populate model context. |

New conversation resets working dialogue and evidence, not SQLite or remote traces. A UI rerun preserves the background job; process restart can lose it. Promotion from a reviewed failure to a dataset requires manually selecting the question, expected behavior, evidence and visibility. There is no automatic learning or promotion path.

## Behavior contracts and evidence

Given/When/Then checks make the boundaries reproducible. Test names below are in the linked files; scripted-model tests establish control flow, not model reliability.

| Given / when / then | Test or recorded evidence | Scope |
| --- | --- | --- |
| A model requests an unknown tool or extra execution permission → dispatch rejects it. | [test_agent.py](../tests/test_agent.py): `test_unknown_tool_requests_cannot_extend_runtime_permissions`, `test_model_cannot_override_execution_limits` | Capability boundary. |
| A passage includes malicious instructions → it remains tool-result data and cannot grant a tool. | `test_injected_document_instructions_remain_tool_data_and_cannot_grant_a_tool` | No general prompt-injection immunity. |
| A draft contains malformed or unknown citations → checks demand repair before model auditing. | `test_malformed_citation_requires_repair_before_auditor_runs`; [test_evaluate.py](../tests/test_evaluate.py) checks earlier delivered turns too. | Citation identity, not semantic support. |
| A grouped citation contains an unread or undeclared ID → the group cannot bypass the same checks. | `test_plain_citation_groups_require_every_id_to_be_known_and_declared`, `test_overview_grouped_citation_reaches_the_same_semantic_verifier` | CommonMark citation contract version 3. |
| A support-mode attempt exhausts its work → any partial recovery must pass a fresh full check. | `test_partial_recovery_requires_its_own_full_check`; [one real recovery replay](../results/recovery-check-v1/receipt.json) | Narrow recovery, not whole-task success. |
| A later citation failure follows supported claims → retain a proposal, then accept or reject its fresh recheck. | `test_later_citation_failure_preserves_supported_facts_for_fresh_recovery` | Retention is not automatic release. |
| A new conversation starts → old dialogue and citation authority are absent. | `test_fresh_session_inherits_neither_dialogue_nor_citation_authority` | Working context, not deletion of saved records. |
| More than six exchanges finish → retained dialogue stays bounded and original evidence identifiable. | `test_incremental_memory_keeps_six_exchanges_and_original_read_evidence` | No byte cap on the source ledger. |
| A saved answer is reviewed → original evidence remains unchanged. | [test_library.py](../tests/test_library.py): `test_explicit_reviews_keep_history_and_do_not_rewrite_source_check` | Preservation, not truth of the review. |
| Two tabs review one answer → both dated entries survive. | `test_simultaneous_reviews_preserve_both_history_entries` | Atomic SQLite read/append/write. |
| The UI navigates while work runs → one job continues and attempts to save before display. | [test_app.py](../tests/test_app.py): `test_pending_work_survives_navigation_and_saves_before_display`; [live navigation check](../results/ui-recovery-v1/browser.json) | Save failures are reported; no process-crash recovery. |
| Typed chat and a preset arrive together → typed text wins and the preset cannot submit later. | `test_each_submission_runs_once_across_layout_changes_and_reset` | One session's input-consumption boundary. |
| Questions or answers contain Markdown images → conversation and library views show text while preserving code and links. | `test_chat_and_library_images_become_text_without_losing_code_or_links` | Inline/reference images, escaped examples, raw HTML and indentation. |
| A recognized secret enters a request → masking precedes the outgoing and persistence paths. | [test_redaction.py](../tests/test_redaction.py); [live backend canary check](../results/ui-recovery-v1/backend.json) | Recognized formats and inspected sinks only. |
| An evaluation's earlier turn fails but its last turn succeeds → the run still reports an operational error. | [test_evaluate.py](../tests/test_evaluate.py): `test_cli_preserves_all_turn_errors_and_configured_judge_from_prediction` | Also checks configured recovery-model propagation; quality failures remain distinct. |

Changes to capabilities, memory or release policy require updated boundary tests and attributable behavioral evidence. The [October 28 review](../results/thorough-pass-2026-10-28/review.md) records the latest repair validation. [Versioning](VERSIONING.md) explains what each identity covers; version labels themselves grant no permissions.
