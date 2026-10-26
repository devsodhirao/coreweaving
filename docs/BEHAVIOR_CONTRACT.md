# Purpose, permissions, and memory

Coreweaving helps a person understand and use Weave documentation. A useful answer should explain the next action, its reason, and the evidence and caveats needed to apply it. The agent may research and propose code; it does not administer the user's infrastructure.

This follows our existing BDD pathway approach: **intent → trigger → real state changes → observable consequence → evidence → known gap**. The earlier Neural Viscera pathway contract and ordinary pytest Given/When/Then style supplied the pattern. We reuse the method, without importing another product's runtime or treating a linked test as proof of general correctness.

## Permission boundary

| Capability | Runtime permission | Observable limit |
| --- | --- | --- |
| Search/read | Read the locked local Weave corpus through two named tools | Page IDs resolve through the corpus; no arbitrary URL or host-file tool |
| Try code | Run a small Python standard-library example in a disposable Docker container | No network, host mounts, credentials, package installation, or privilege; fixed resource/time/output limits |
| Answer | Submit a structured draft for a separate check | The conversational app refuses verification-off configuration; partial material support and material coverage gaps require repair in their applicable modes |
| Account/deployment actions | No tool or dispatch route | Unknown tool names and additional arguments fail; neither user text nor retrieved text changes the tool list |
| Telemetry/model requests | Application-configured Anthropic and Weave connections | These background services use setup credentials. They are not a general network tool available to the agent |
| Experiment spend | Application request reservations and returned-usage ledger | A shared pilot budget covers agent and judge calls; unknown usage stops subsequent calls. This is an estimate limit, not an invoice cap |

The purpose restriction and interpretation of untrusted text are **model guidance**, not a security classifier. The tool allowlist and container restrictions are **runtime controls**. A model can still misunderstand a question or answer outside its intended topic; no test below claims otherwise. General infrastructure operations would require new application capabilities and a new permission decision, not a prompt saying “you may now deploy.”

## Memory grows deliberately

1. **Working conversation:** retain six complete question/answer exchanges and a stable conversation ID. A source ledger retains original passages for that session; it is not yet size-limited. The current coverage input contains current reads and sources cited in retained dialogue, not every old passage. Starting a new conversation clears working dialogue and evidence.
2. **Local learning record:** save each UI answer, preceding context, original sources, implementation/snapshot identity, trace, and usage. It begins **unreviewed**. Explicit review changes a separate assessment/history; it never rewrites the original answer or the model's check.
3. **Reusable evaluation knowledge:** a reviewed failure can motivate a source-backed test case. Promotion requires selecting and reviewing the question, expected behavior, evidence and visibility, then explicitly adding it to a dataset and evaluating a version. This workflow is currently manual; there is no automatic promotion button.
4. **Future retrieval memory:** retrieving reviewed answers, inferred preferences, summaries or graph relationships is not implemented. It would need provenance, freshness, correction/deletion controls and a measured benefit. A review label alone must never replace official documentation authority.

New conversation is a working-memory reset, not deletion of local library records or the public Weave trace. Those are separate stores. The current UI does not provide library or remote-trace deletion. This distinction matters before adding personal memory.

## Behavior contracts and evidence

| ID / intent | Given / When / Then | Actual test or experiment | What it does not prove |
| --- | --- | --- | --- |
| CW-PERM-01 · stay within authority | Given the fixed tools, when a response requests a new capability, then no permitted backend is invoked and the unknown tool is rejected | `tests/test_agent.py::test_unknown_tool_requests_cannot_extend_runtime_permissions` | A model will always stay on topic |
| CW-PERM-02 · keep execution bounded | Given offline Python, when a tool request includes a timeout override, then dispatch rejects the extra argument; real container probes cannot see host credentials or use the network | `test_model_cannot_override_execution_limits`; `tests/test_sandbox.py` | Live SDK integration correctness or perfect container isolation |
| CW-DATA-01 · preserve the trust boundary | Given a malicious passage, when it proposes a new tool, then it remains tool-result data and cannot grant that capability | `test_injected_document_instructions_remain_tool_data_and_cannot_grant_a_tool`; regression case `13-injected-instruction` separately tests a malicious note quoted in user input | General semantic prompt-injection immunity |
| CW-MEM-01 · fresh context | Given an earlier conversation, when a fresh session begins, then earlier dialogue and citation authority are absent | `test_fresh_session_inherits_neither_dialogue_nor_citation_authority` | Erasure of separate saved or remote records |
| CW-MEM-02 · bounded dialogue | Given an ongoing conversation, when eight exchanges finish, then only six exchanges are retained and original source evidence remains identifiable | `test_incremental_memory_keeps_six_exchanges_and_original_read_evidence` | A byte bound on the entire session source ledger |
| CW-MEM-03 · review without rewriting history | Given a saved answer, when the owner reviews it or saving repeats, then the original evidence stays fixed and review history records the explicit change | `tests/test_library.py::test_explicit_reviews_keep_history_and_do_not_rewrite_source_check`; `test_repeat_save_is_idempotent_and_cannot_overwrite_review_or_evidence` | Automatic promotion, truth of a “useful” label, or durable personal preferences |
| CW-ANS-01 · answer the whole task | Given a supported draft missing a requested part, when coverage mode audits it, then the omission returns as repair feedback before release | `test_coverage_omission_returns_feedback_then_releases_repaired_answer`; frozen `cap-04-whole-workflow` and `cap-05-context-change` | Coverage of unseen docs; fake-model checks establish control flow, paid evaluation measures actual judgments |
| CW-ANS-02 · reject malformed provenance | Given malformed, disguised, unknown or mismatched source IDs, when a checked mode receives the draft, then the shared citation contract requires repair; evaluation checks every delivered turn | `test_malformed_citation_requires_repair_before_auditor_runs`; `test_candidate_contract_requires_typed_references_and_forbids_extras`; `test_source_like_rendering_cannot_disguise_citation`; `tests/test_evaluate.py::test_citation_integrity_checks_earlier_delivered_turns_and_labels_legacy` | Full Markdown parsing or semantic truth; ordinary code/docs links are allowed, source-like link labels are reserved, and experimental off still releases unchecked drafts |
| CW-ANS-03 · distinguish facts from research limits | Given a supported statement about recorded search/read actions, when the verifier classifies it as research process, then it may pass without a documentation citation; product claims still require evidence | `test_search_limit_claim_requires_supported_recorded_process` | Reliable semantic classification by a fallible verifier; a search miss never proves an API does not exist |
| CW-SEC-01 · mask credentials before leaving the app | Given a configured secret or recognized credential form, when a request enters the agent/provider or a record is saved/exported, then masking happens before that sink | `tests/test_redaction.py`; `test_secret_masking_precedes_agent_messages_history_and_result`; `tests/test_llm.py::test_provider_and_agent_span_payloads_are_sanitized_before_export`; `tests/test_library.py` | General PII detection, unknown encoded/split secrets, or unlabelled unknown legacy 40-hex keys |
| CW-UI-01 · preserve an in-flight answer | Given a pending answer, when the user opens the library and returns, then one worker continues and saves the result before rendering; a second question is disabled | `tests/test_app.py::test_pending_work_survives_navigation_and_saves_before_display` | Process-crash recovery or restoring a browser session after a restart |
| CW-COST-01 · pay for deliberate work | Given an existing answer, when the app rerenders or its review changes, then no agent request repeats; a failed/ungraded paid attempt remains in cost totals | `tests/test_app.py::test_each_submission_runs_once_across_layout_changes_and_reset`; `tests/test_compare.py::test_unscored_paid_prediction_remains_in_costs_and_attempts` | Exact invoices or missing provider-side charges |
| CW-COST-02 · keep cache accounting consistent | Given provider usage with cache reads/writes, when a chat span is exported, then its generic input count includes those tokens while the raw receipt stays unchanged | `tests/test_llm.py::test_trace_input_includes_cache_but_provider_receipt_stays_native` | Correction of historical spans or exact invoices |

The test names above map to real production paths. Unit tests use scripted model responses to test control flow; Docker tests exercise real containment; independent assertion evaluations measure generated answers. Browser checks exercise the visible interaction. Keep these evidence levels separate.

## Why this design

**Product:** a small, dependable scope helps someone decide whether the answer is useful and what to do next. Source/coverage status, human review and freshness remain distinct.

**Education:** the answer explains the next step; expandable evidence and the field guide explain how it was produced. A learner can ask follow-ups without being forced to study tracing internals first.

**AI engineering:** permissions live in dispatch and containment, memory has explicit owners, and changes are measured against frozen cases. Weave provides the inspectable record and online monitoring; model judgments remain fallible.

The current coverage pilot, cache probe and judge calibration are recorded separately under `results/`. Consult their exact source and dataset hashes rather than assuming every test result describes every later checkout.

## Versioned behavior

A capability or memory-policy change also changes the contract and the relevant evidence. The [versioning contract](VERSIONING.md) distinguishes a release from source/prompt/configuration identity, documentation freshness, evaluation rules and immutable answer history. Version labels do not grant permission.
