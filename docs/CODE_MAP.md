# From the brief to the code

Use the [README](../README.md) for setup and current results. This map names the functions, ownership boundaries and reasons behind the implementation; function names remain useful when line numbers change.

## Three paths, three different questions

| Path | Purpose | Entry point |
| --- | --- | --- |
| Conversation | Research, check and answer the user's question | [Agent.run](../src/coreweaving/agent.py) |
| Offline evaluation | Measure answers against frozen tasks and references | [run_evaluation](../src/coreweaving/evaluate.py) |
| Online monitoring | Flag completed turns for developer review | [signals.setup](../src/coreweaving/signals.py) |

Only the verifier participates in answer release; the web app refuses verification-off mode. The evaluation judge and Signal do not block delivery. Source support, task completion and monitoring tags measure different things.

## Follow one question

| Step | Named functions | Responsibility |
| --- | --- | --- |
| Initialize | [settings, init_weave](../src/coreweaving/config.py); [app.resources](../app.py) | Load limits, hash-checked corpus and tracing client. Streamlit caches resources. |
| Submit once | [app.run_question](../app.py) | Run one background job; navigation inspects it without repeating the request. |
| Prepare context | [Session, Agent.run](../src/coreweaving/agent.py) | Mask credentials, retain six exchanges and open a turn with version attributes. |
| Plan | [LanguageModel.call](../src/coreweaving/llm.py) | Send messages/tools to Anthropic; record returned tool requests, usage and caching. |
| Gather evidence | [Agent.execute](../src/coreweaving/agent.py) → [Corpus.search/read](../src/coreweaving/corpus.py) or [run_python](../src/coreweaving/sandbox.py) | Validate exact tool arguments; search, read or execute. Reads mint `S` citation IDs; executions mint `C` IDs. |
| Check a draft | [Candidate, citation_contract, Agent.verify](../src/coreweaving/agent.py) | Validate citation syntax/identity, then audit claims against evidence. Cited prose drafts enter the same checks as `submit_answer`. |
| Repair or stop | [Agent.run, partial_candidate](../src/coreweaving/agent.py) | Apply rejection feedback within limits. Support mode permits one final check of up to four supported facts, labeled partial. |
| Persist and display | [save_answer](../src/coreweaving/library.py); [show_result, show_analysis](../app.py) | Attempt local save and trace flush before display; report failures. Keep sources and diagnostics separate from the answer. |

## Data and ownership

| Owner | State and boundary |
| --- | --- |
| [Session](../src/coreweaving/agent.py) | In-process conversation ID, six complete exchanges and original evidence. The evidence ledger has no size cap; restart loses working memory. |
| [Corpus / Passage](../src/coreweaving/corpus.py) | Frozen text, URL, hash, page/section identity and introductory context. A heading establishes navigation, not unread content. |
| [Candidate / Verification](../src/coreweaving/agent.py) | Typed proposal and audit. Unknown citations and partial/unsupported material claims prevent checked release; support mode does not enforce completeness. |
| [Agent.run result](../src/coreweaving/agent.py) | One receipt supplies the UI, library and evaluation with answer, evidence, actions, checks, versions, trace IDs and usage. |
| [library.py](../src/coreweaving/library.py) | SQLite preserves original answers and separate review history. Reviews do not become retrieval facts, instructions or Weave feedback automatically. |

New conversation clears working context, not saved answers or public traces. Runtime tools cannot fetch arbitrary URLs, read host files or administer accounts. Docker execution has no network, host mounts or credentials and does not install Weave. Credential masking is not general PII protection. See the [behavior contract](BEHAVIOR_CONTRACT.md).

## Design rationale and open questions

**Reasoned** means an engineering choice; **Observed** means recorded behavior; **Compared** means alternatives were run under the stated experiment. These labels are not confidence scores.

| Choice | Basis and useful evidence | Limit |
| --- | --- | --- |
| Sonnet + explicit Python loop | **Reasoned:** native tool calls and lower [recorded token prices](../src/coreweaving/metrics.py) than Opus suit repeated planning. One loop owns control and permissions. | No model/framework comparison; serial calls still make answers slow. Opus judges and checks final recovery, within the same model family. |
| Frozen Markdown + BM25 | **Reasoned:** inspectable API-name matching, local operation and reproducible inputs. **Observed:** [offline restore](../results/brief-e2e-v1/fresh-setup-final.json) checks the bundled bytes. | No retrieval-method benchmark, live freshness or version selector. |
| Separate source verifier | **Compared:** [historical pilot](../results/coverage-pilot-v1/review.md) favored support mode for citation integrity; factual assertions tied with off, while coverage refused answerable tasks. | Small reused tasks; verification adds latency and can both miss errors and reject useful answers. |
| Weave traces, evaluation and Signal | **Observed:** [end-to-end review](../results/brief-e2e-v1/review.md) connects failures to traces, policy repairs and subsequent checks. | No comparison against another platform or general assistant; monitor accuracy remains unmeasured beyond selected examples. |
| Answer first, optional analysis | **Reasoned:** let users act before inspecting diagnostics. **Observed:** [browser review](../results/brief-e2e-v1/ui-final/manual-review.json) exercises navigation and follow-ups. | Browser checks are not a usability study; answers remain slow and verbose. |
| Bounded tools, memory and recovery | **Reasoned:** restrict capabilities and repeated work; retain supported facts when a complete answer fails. | Ten planning calls, eighteen tool calls, two repairs and four recovery facts are heuristics, not optimized limits or a security guarantee. |

## Retrieval alternatives considered

BM25 is the implemented baseline, not a measured winner. Dense embeddings could address paraphrases and can use a local index without a hosted vector database. Hybrid retrieval with rank fusion is a proportionate comparison; contextual indexing would add chunk context *before* search, unlike our post-search `page_context`. Validated link expansion would be simpler to try than an extracted knowledge graph. None of these alternatives was benchmarked here. Hold the snapshot, chunks, queries and returned-text budget fixed, measure relevant-section coverage and latency, then assess answer quality; finding a page does not establish that the answer used its facts.

## How the agent reads documentation

[fetch_docs.py](../scripts/fetch_docs.py) supports locked offline restoration of 351 bundled Markdown pages; [Corpus](../src/coreweaving/corpus.py) checks their manifest hashes and indexes titles, headings and passage text. `search` returns navigation hints; `read` returns evidence and `outline` exposes headings. Only reads create documentation citation authority.

- Heading splitting respects ordinary code fences, but the later 7,000-character cap can cut examples inside fences. The [structure check](../results/submission-repair-v1/corpus-structure-check.json) records the affected boundaries.
- Introductory context stops at 2,000 characters; it cannot preserve every prerequisite. Internal links remain text, not validated page IDs for traversal.
- Section numbers belong to a snapshot; `S`/`C` IDs belong to a conversation. Hashes establish identity, not freshness or correctness.
- Runtime reads are local. Refreshing the corpus requires maintainer work, archive rebuilding and an app cache reset; [versioning](VERSIONING.md#documentation-freshness-and-version-support) describes the single-snapshot and compatibility limits.

## Weave use and evidence

**A conversation is a grouping, not a parent span.** `start_conversation` associates turns through `conversation_id`; each `start_turn` creates a separate turn trace. `start_llm`, `start_tool` and the verifier's `start_subagent` form spans within that turn. Model memory comes from `Session.history`, not trace grouping. [agent.py](../src/coreweaving/agent.py), [llm.py](../src/coreweaving/llm.py) and the [backend readback](../results/brief-e2e-v1/backend-final.json) show this structure.

[init_weave](../src/coreweaving/config.py) disables implicit integration patching; the transport disables duplicate provider tracing. Turn attributes identify source, prompts, configuration, corpus and usage. Evaluation uses `weave.Dataset`, `weave.Evaluation` and ordinary `@weave.op` judge Calls; `weave.eval.*` attributes connect agent turns to evaluation rows.

[signals.setup](../src/coreweaving/signals.py) activates a `Monitor` on `weave.genai.turn_ended`, filtered to this agent. It checks exactly three conditions: an assistant-reported operational failure, explicit research/repair-limit exhaustion, or factual Weave instructions with zero `[S#]` markers. It does not assess correctness or general completeness. The [policy audit and calibration](../results/brief-e2e-v1/review.md#online-monitoring) preserve false positives and the narrower checks; general precision/recall remains unmeasured.

CoreWeave supplies Weave and Signal inference; Anthropic supplies the assistant and offline judge. Human feedback is still local, prompts use Git/hashes and no Leaderboard is published. The [evidence index](../results/README.md) retains current and historical readbacks without treating documentation edits as new measurements.

## Follow the evaluation

In [evaluate.py](../src/coreweaving/evaluate.py): `dataset_rows` resolves frozen questions, assertions and judge-only references → `trial_rows` expands repeats → `DocumentationModel.predict` creates a fresh session per case and runs follow-ups → `QualityJudge.score` grades assertions and quality, while `integrity` checks citation/execution structure. References are withheld from the agent.

`persist_record` preserves attempts; `aggregate_records` and `reconcile_budget_usage` retain partial work and returned usage. `sync_completed_evaluation` can redeliver an original completion after transport failure without rerunning answers. Operational failure exits nonzero; a completed answer-quality failure remains a valid measurement. The [evaluation design](EVALUATION_DESIGN.md) explains the small, reused suites and same-family judge limitation.

## Supporting files and why they exist

| File | Responsibility |
| --- | --- |
| [__main__.py](../src/coreweaving/__main__.py) | Terminal entry point using the same agent. |
| [metrics.py](../src/coreweaving/metrics.py) / [budget.py](../src/coreweaving/budget.py) | Returned usage, cache pricing and experiment reservations; estimated spend is not an account billing cap. |
| [compare.py](../src/coreweaving/compare.py) / [check_experiment.py](../src/coreweaving/check_experiment.py) | Pilot comparisons and explicit paid cache/judge probes; neither is an ordinary app path. |
| [pyproject.toml](../pyproject.toml) / [uv.lock](../uv.lock) / [.env.example](../.env.example) | Dependencies and configuration names; real credentials stay outside Git. |

## Find the tests by behavior

[Agent tests](../tests/test_agent.py) cover release and permission boundaries; [app tests](../tests/test_app.py) cover once-only work and navigation; [evaluation tests](../tests/test_evaluate.py) cover grading and evidence preservation. The [behavior contract](BEHAVIOR_CONTRACT.md) maps detailed Given/When/Then checks. These establish mechanics; separately versioned real runs measure answer quality.
