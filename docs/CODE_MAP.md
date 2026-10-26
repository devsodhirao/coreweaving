# From the brief to the code

Read the [README](../README.md) for setup and measured results. Use this map to explain how a question moves through the implementation, then follow the linked files and named functions. Function names are the durable navigation targets; source line numbers change as the code is edited.

## Three paths, three different questions

| Path | Question it answers | Main code |
| --- | --- | --- |
| Conversation and verification | What can we answer from the evidence available now? | [app.py](../app.py), [Agent](../src/coreweaving/agent.py), [Corpus](../src/coreweaving/corpus.py), [LanguageModel](../src/coreweaving/llm.py) |
| Offline evaluation | How well did the agent handle the frozen tasks? | [evaluate.py](../src/coreweaving/evaluate.py), [evals/](../evals), [results/](../results/README.md) |
| Online monitoring | Which completed turns deserve developer review? | [signals.py](../src/coreweaving/signals.py), configured Weave Signal |

The verifier participates in answer release. The evaluation judge and online Signal do not block the user response. A passing source check can still leave the task incomplete.

## Design rationale and open questions

These are engineering reasons for the choices, with the evidence needed to reconsider them. The verifier policies received a paired answer-quality comparison; the project has no model, retrieval-method or general-assistant benchmark.

| Choice and code | Why it serves the task | Tradeoff and what would change the decision |
| --- | --- | --- |
| Sonnet and one explicit loop — `Agent.run`, `LanguageModel.call` | The agent can search, read several pages and revise a draft as evidence arrives. Direct Python keeps decisions and permissions visible. Sonnet supports the tool API and has lower recorded token prices than Opus, containing the cost of repeated calls. | Repeated calls add latency and cost. Compare task success, cost and time before claiming this model or a specialist-agent design is better. |
| Frozen structured corpus and BM25 — `Corpus`, `fetch_docs.py` | Stable passages, URLs and hashes make citations inspectable and experiments repeatable. Lexical search needs no embedding service and handles literal API names directly. | Snapshot freshness and paraphrases are weaknesses. Use source-labeled retrieval failures to test contextual chunks or hybrid search; a live-site check is useful when freshness matters. |
| Separate grounded verifier — `Agent.verify`, `citation_contract` | A second call checks the draft against actual passages, while deterministic checks catch malformed and unknown citations. Specific rejection feedback supports repair. | The verifier adds work and can miss omissions or reject useful drafts. The [pilot](../results/coverage-pilot-v1/review.md) supports keeping support mode as this prototype's default; it is too small to establish a general winner. |
| Traces, offline evaluation and online Signals — `llm.py`, `evaluate.py`, `signals.py` | Traces explain a turn; frozen tasks compare changes; Signals identify completed turns for review. Together they connect a failure to the behavior that produced it. | Instrumentation and backend reconciliation add maintenance. The judge shares the agent's model family, and Signal detection accuracy is unmeasured. [Observed use](#weave-use-and-evidence) explains the value already obtained. |
| Answer first, separate analysis — `show_result`, `show_analysis` | A readable answer serves the user; sources, checks, usage and trace links remain available for inspection without another model call. | Another window adds a navigation step. [Browser checks](../results/final-readonly-ui.json) establish mechanics, not adoption or a usability-study result. |
| Bounded tools and deliberate memory — `Agent.execute`, `Session`, `sandbox.py`, `library.py` | Application code defines capabilities. Original source evidence travels with follow-ups; human reviews remain separate from source facts. | Containers and credential masking reduce specific risks without making a general security guarantee. Working memory is process-local and its source ledger still needs a size bound. |
| Research and recovery limits — `Settings`, `Agent.run`, `partial_candidate` | Limits bound repeated work; one strictly rechecked partial recovery can preserve useful supported facts when the task remains incomplete. | Ten planning calls, eighteen tool calls, two repairs and four recovery facts are heuristics. Calibrate against completion, refusal rate, latency and cost before calling them optimal. |

**Scope discipline:** the assistant, tracing, Signal and required evaluation are the core submission. The library, cost accounting, experiment reconciliation and artifacts explain development choices but increase the code to maintain. Voice, adaptive UI, specialist routing and graph retrieval remain proposals. The build exceeded the brief's time budget; [dated milestones](AI_BUILD_LOG.md) make that explicit.

## Follow one question

| Step | Function to open | Input → output, and the boundary it owns |
| --- | --- | --- |
| 1. Initialize | `config.settings`, `config.init_weave`; `app.resources` | Environment/configuration → fixed limits, corpus and Weave client. Initialization precedes spans; credentials stay out of the settings object. |
| 2. Submit once | `app.run_question`; bottom of [app.py](../app.py) | Question + session → background job. UI reruns inspect the pending job instead of repeating the paid request. |
| 3. Open a turn | `Agent.run`; `Session` in [agent.py](../src/coreweaving/agent.py) | Masked question + six exchanges → planner messages. Source, prompt, configuration and snapshot identities become trace attributes. |
| 4. Ask the model | `LanguageModel.call` in [llm.py](../src/coreweaving/llm.py) | Messages + tool schemas → typed tool requests and provider usage. Weave records actual messages and tool-call IDs. |
| 5. Gather evidence | `Agent.execute` → `Corpus.search/read` or `sandbox.run_python` | Exact allowed arguments → navigation hints, original document passages or an isolated execution result. Reads receive stable `S` IDs; executions receive `C` IDs. |
| 6. Propose and check | `Candidate`, `citation_contract`, `Agent.verify` | Draft + evidence → validated citations and a separate model verdict. Unknown IDs, malformed markers and unsupported/partial material claims prevent acceptance. |
| 7. Repair or stop | `Agent.run`, `partial_candidate` | Specific rejection feedback → another bounded attempt. Support mode can propose up to four supported facts for one additional strict check; any released recovery is labeled partial. |
| 8. Save and inspect | `library.save_answer`; `app.show_result/show_analysis` | Answer receipt → immutable local result and separate UI diagnostics. Inspection does not invoke the agent. |

`Agent.run` is deliberately linear: prepare the turn, run the traced loop, then retain dialogue and return a receipt. `execute` owns capabilities and `verify` owns release checks. The file is still substantial because it also contains prompts, schemas and citation helpers; use these named boundaries rather than reading every prompt first.

## Data and ownership

| Data | Owner | Lifetime / limitation |
| --- | --- | --- |
| `Session` | [agent.py](../src/coreweaving/agent.py) | In-process conversation ID, six exchanges and source ledger. The ledger is not size-capped; restart loses working memory. |
| `Passage` and corpus snapshot | [corpus.py](../src/coreweaving/corpus.py) | Frozen page/section, original URL, content hash and page introduction. Headings guide navigation; they do not establish unread content. |
| `Candidate` / `Verification` | [agent.py](../src/coreweaving/agent.py) | Typed proposal and source audit. Model schema descriptions can affect prompts, so editing these contracts is a behavior change. |
| Turn result dictionary | `Agent.run` | Answer ID, text, status, context, cited/read evidence, actions, checks, trace IDs, versions and usage. UI, library and evaluator consume this same receipt. |
| Provider usage / cost estimate | [metrics.py](../src/coreweaving/metrics.py) | Returned planner/verifier calls, including repairs. Raw disjoint cache buckets stay separate from Weave's inclusive input-token representation. |
| Human review | [library.py](../src/coreweaving/library.py) | Separate SQLite review history. It never silently becomes source evidence, a model instruction or a Weave feedback record. |

## Weave use and evidence

The implementation follows the current [agent tracing guide](https://docs.coreweave.com/products/wandb/weave/guides/tracking/trace-agents), [evaluation guide](https://docs.coreweave.com/products/wandb/weave/guides/core-types/evaluations) and [Signals guide](https://docs.coreweave.com/products/wandb/weave/guides/tracking/view-agent-signals), checked October 26, 2026.

| Capability | Exact implementation | Evidence to open / what it establishes |
| --- | --- | --- |
| Initialization | `config.init_weave` disables implicit integration patching; `LanguageModel` disables duplicate provider tracing | [Model-span readback](../results/preset-check-v4/backend.json): returned model requests and usage reconcile with stored spans. |
| New agent data model | `Agent.run`: `start_conversation`, `start_turn`, `start_tool`; `LanguageModel.call`: `start_llm` | [Agent readback](../results/agent-trace-readback-v2.json): real hierarchy, identities and evaluation attributes. Tools execute after model spans close and retain their tool-call IDs. |
| Verifier ownership | `Agent.verify`: `start_subagent`; `LanguageModel.call(span_parent=verifier)` | [Final targeted readback](../results/preset-check-v4/backend.json): verifier chats have the verifier span as parent. This is one verification role, not a specialist-agent network. |
| Dataset/model/scorer | `run_evaluation`: `weave.Dataset`, `weave.publish`, `weave.Evaluation`; `DocumentationModel` and `QualityJudge` | [Regression summary](../results/regression-v2/summary.json): dataset reference, evaluation Call ID, per-case results and version identities. |
| Agent ↔ evaluation linkage | `DocumentationModel.predict`: actual evaluation IDs and `weave.eval.*` attributes passed into `Agent.run` | [Agent readback](../results/agent-trace-readback-v2.json): sampled trace attributes match their evaluation rows. |
| Independent judge tracing | `QualityJudge.score` and `judge_provider_request` use ordinary `@weave.op` Calls | [Judge readback](../results/judge-trace-readback-v2.json): scored Calls and provider children, without a second evaluator Agent cluttering the Agents view. |
| Online monitor | `signals.setup`: `Monitor`, `weave.genai.turn_ended`, server-side `agent_name` filter, sampling 1.0 | [Configuration readback](../results/brief-alignment-check.json) and [real failed-turn feedback](../results/coverage-pilot-v1/live-signal-review.json). The synthetic fixture is separately labeled. |
| Version/cost investigation | `source_fingerprint`, `Agent.run` attributes, `metrics.summarize`, `llm.call` usage conversion | [Navigation/security readback](../results/ui-recovery-v1/backend.json): provider receipts reconcile with native trace costs after the cache-accounting correction. |

This is useful Weave adoption: evidence led to a verifier-policy choice and exposed integration failures. Its limits remain visible. Human feedback is still local; prompts use Git/hashes rather than `StringPrompt` objects; no Leaderboard is published. Signal precision/recall has not been measured. CoreWeave hosts Weave and the Signal's inference; Anthropic supplies the agent and offline judge.

## Follow the evaluation

1. `dataset_rows` resolves the frozen questions and assertions against the same corpus. Reference passages are supplied to the judge; the agent must find its own evidence.
2. `trial_rows` materializes repeat IDs shared across arms. `weave.Evaluation(trials=1)` prevents repeating those already-expanded rows again.
3. `DocumentationModel.predict` creates a fresh session per case, runs every follow-up and preserves each attempt. Evaluation Call IDs connect the resulting agent spans to the scored row.
4. `QualityJudge.score` checks independent assertions plus quality criteria; `integrity` checks citation/execution structure. Reference overlap and verifier adherence are diagnostics, not substitutes for quality.
5. `persist_record` keeps distinct attempt files. `aggregate_records` includes partial work; `reconcile_budget_usage` checks returned usage. `sync_completed_evaluation` can replay an original completion after a delivery failure—it does not rerun the agent.

These functions are in [evaluate.py](../src/coreweaving/evaluate.py). Its length mostly reflects scoring and evidence preservation; the app does not import it. The 13-case regression and six-case capability pilot are small development instruments with a same-family judge, not a production accuracy estimate.

## Supporting files and why they exist

| File | Role | When to read it |
| --- | --- | --- |
| [__main__.py](../src/coreweaving/__main__.py) | Terminal entry point using the same `Agent.run` | To demonstrate the runtime without Streamlit. |
| [metrics.py](../src/coreweaving/metrics.py) | `MeteredModel`, `estimate_cost`, `summarize` | To explain returned usage, caches, repairs and unknown prices. |
| [budget.py](../src/coreweaving/budget.py) | `ModelBudget.reserve`, `model_budget` | Experiment spending reservations; imported by provider boundaries, so it remains in the package. This is not an account billing cap. |
| [sandbox.py](../src/coreweaving/sandbox.py) | `run_python` | Offline, non-root Docker process with no host mounts/credentials and bounded resources. It does not test installed Weave APIs. |
| [compare.py](../src/coreweaving/compare.py) | `run_comparison`, `compare_records` | The recorded three-arm pilot, paired case identities and missing/error cells. Not imported by the app. |
| [check_experiment.py](../src/coreweaving/check_experiment.py) | `cache_probe`, `calibrate` | Explicit paid synthetic cache/judge checks. Not an ordinary chat path. |
| [fetch_docs.py](../scripts/fetch_docs.py) | Snapshot download and locked restoration | Setup/freshness; runtime page reads never fetch arbitrary URLs. |
| [check_judge.py](../scripts/check_judge.py), [repair_evaluation.py](../scripts/repair_evaluation.py) | Earlier calibration and delivery diagnosis | Historical supporting procedures; not required to answer a question. |
| [pyproject.toml](../pyproject.toml), [uv.lock](../uv.lock), [.env.example](../.env.example) | Package, locked dependencies and variable names | Setup/version reproduction. Real `.env` remains ignored. |

## Find the tests by behavior

| Question to defend | Tests / recorded evidence |
| --- | --- |
| Can a question grant extra capabilities or bypass a failed check? | [test_agent.py](../tests/test_agent.py), [test_sandbox.py](../tests/test_sandbox.py), [behavior contract](BEHAVIOR_CONTRACT.md) |
| Can malformed citations or empty recovery verdicts slip through? | [test_agent.py](../tests/test_agent.py); [recovery review](../results/recovery-check-v1/implementation-review.json) |
| Do navigation and duplicate question labels preserve the right answer? | [test_app.py](../tests/test_app.py); [browser check](../results/final-readonly-ui.json) |
| Are model secrets masked before requests, tracing and persistence? | [test_redaction.py](../tests/test_redaction.py); [backend canary check](../results/ui-recovery-v1/backend.json) |
| Can a judge reuse the agent's own success flag as its grade? | [test_evaluate.py](../tests/test_evaluate.py), [test_datasets.py](../tests/test_datasets.py); [judge calibration](../results/assertion-calibration-v2/calibration.json) |
| Are saved answers and earlier reviews preserved? | [test_library.py](../tests/test_library.py) |
| Are repairs, cache usage and interrupted work counted? | [test_metrics.py](../tests/test_metrics.py), [test_llm.py](../tests/test_llm.py), [test_budget.py](../tests/test_budget.py), [test_compare.py](../tests/test_compare.py) |

Local tests verify mechanics and boundaries. Actual answer quality comes from the separately versioned evaluation/browser records in the [evidence index](../results/README.md). The [readability receipt](../results/readability-review.json) verifies that this documentation pass preserves executable logic and model contracts; historical results retain their original source identities.
