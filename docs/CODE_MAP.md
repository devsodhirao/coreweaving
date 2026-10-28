# From the brief to the code

Use the [README](../README.md) for setup and measured results. Start with `Agent.run`, then follow the paths below. Function names remain useful when line numbers change.

**Measured runtime:** commit `fe4b7b5ea5fe1b661945a7129cc9d8a29f6565ba`; source SHA256: `860e9ee6c1134ca44ed04ac9dd22103e2c8acfe5f64fe40a0969941034af53ff`. The regression scored 12/13 and 47/48 assertions. Historical runs in the [evidence index](../results/README.md) retain their original source and policy.

## Three paths, three different questions

| Path | Purpose | Entry point |
| --- | --- | --- |
| Conversation | Research, check and answer the user's question | [Agent.run](../src/coreweaving/agent.py) |
| Offline evaluation | Measure answers against frozen tasks and references | [run_evaluation](../src/coreweaving/evaluate.py) |
| Online monitoring | Flag completed turns for developer review | [signals.setup](../src/coreweaving/signals.py) |

The Signal listens for `weave.genai.turn_ended`. Its server filter selects this agent's ERROR turns or four runtime `review_reason` values: operational failure, exhaustion, incompleteness or uncited answer. Non-error turns labeled `none` are excluded before scoring. Eligibility is deterministic; the runtime classification can miss semantic defects, and LLM explanation/tag generation can fail. This monitor does not block answers.

## Follow one conversation turn

In [agent.py](../src/coreweaving/agent.py), `Agent.run` owns the turn and shared research/repair limits:

1. `plan_task` freezes requested outcomes before retrieval. For workflow overviews, the model selects subjects and the application adds **input, execution trigger and output** for each. User-request quotes constrain provenance; task interpretation can still be wrong.
2. `execute` dispatches tools; `Session.add_passage` assigns evidence IDs after reads. Search hits, outlines and links guide navigation but do not substitute for read evidence.
3. `verify` applies `citation_contract`, then audits claims, applicability and every frozen outcome. Workflow facets require literal quotes from read, cited passages. Quotes and IDs prove provenance and structure; semantic support and completeness remain model judgments.
4. Failed verdicts can request typed research against a missing outcome or unsupported claim, within existing navigation and work limits. Cited prose uses this same release path without a rewrite. Application-owned actions never invent provider tool-call IDs.
5. Research dispatches have their own limit; submissions and revisions use the remaining planning/revision allowance. The last planner call offers submission only. In support mode, one terminal judge call can strictly recheck a full draft after an auditor-record failure, or recheck a `partial_candidate`. The full path cannot waive outcomes or fall through to another audit. `completion_state` retains unmet outcomes.

`LanguageModel.call` in [llm.py](../src/coreweaving/llm.py) traces calls and usage. The assistant model handles planning, research and ordinary verification; the configured judge handles offline grading and bounded recovery. Separate verifier calls are not an independent model family.

`live_verdict_schema` and `parse_live_verdict` require and validate known audit fields while historical readers retain defaults. Unknown root, claim and outcome annotations are discarded; they cannot set application-owned mode/text or authorize actions. Typed research requests remain strict. Workflow output allowance scales with facet count; missing, invalid or truncated required data fails closed.

A truncated planner response is discarded before history insertion or tool execution. Once per turn, the next existing planning slot may retry with a 4,800-token cap instead of 2,400; later calls return to 2,400. A second truncation or truncation in the final slot stops explicitly. A completed retry still passes through ordinary verification.

## Application and source boundaries

| Start here | Responsibility and limit |
| --- | --- |
| [app.py](../app.py): `run_question`, `show_pending_turn`, `show_result` | Once-only background work, progress and evidence display; persistence failures remain visible. `show_markdown` suppresses chat images, preserving text, code and user-followed links. |
| [corpus.py](../src/coreweaving/corpus.py): `Corpus`, `search`, `read` | Hash-checked local snapshot, lexical search and exact passages. [fetch_docs.py](../scripts/fetch_docs.py): `restore_locked_weave` restores the bundled 351-page snapshot offline; runtime retrieval does not browse the live site. |
| [library.py](../src/coreweaving/library.py): `save_answer`, `review_answer` | Local SQLite records; separate review history uses an atomic transaction. Reviews do not automatically become agent memory or training data. |
| [config.py](../src/coreweaving/config.py): `redact_sensitive`, `source_fingerprint` | Recognized credential masking and runtime identity. Masking is not a blanket PII guarantee. |
| [sandbox.py](../src/coreweaving/sandbox.py): `run_python` | Optional Docker execution with no network, host mounts or injected credentials, plus resource limits. Its standard-library environment cannot validate Weave SDK/API examples. |

## Follow the evaluation

In [evaluate.py](../src/coreweaving/evaluate.py): `dataset_rows` resolves questions, assertions and judge-only references → `trial_rows` expands repeats → `DocumentationModel.predict` runs each case and follow-ups → `QualityJudge.score` grades answers. `integrity` checks citation/execution structure. References are withheld from the agent.

`persist_record`, `aggregate_records` and `reconcile_budget_usage` preserve partial work and usage. `sync_completed_evaluation` redelivers a completion without rerunning answers. Any operational turn error makes the run exit nonzero; a graded quality failure remains valid evidence. Predictions pass configured `JUDGE_MODEL` into recovery. See [evaluation design](EVALUATION_DESIGN.md) for suite reuse and judge limitations.

## Supporting files and why they exist

| File | Responsibility |
| --- | --- |
| [__main__.py](../src/coreweaving/__main__.py) | Terminal entry point using the same agent. |
| [metrics.py](../src/coreweaving/metrics.py) / [budget.py](../src/coreweaving/budget.py) | Returned usage, cache pricing and experiment reservations; estimated spend is not an account billing cap. |
| [compare.py](../src/coreweaving/compare.py) / [check_experiment.py](../src/coreweaving/check_experiment.py) | Pilot comparisons and explicit paid cache/judge probes; neither is an ordinary app path. |
| [pyproject.toml](../pyproject.toml) / [uv.lock](../uv.lock) / [.env.example](../.env.example) | Dependencies and configuration names; real credentials stay outside Git. |

## Retrieval alternatives considered

BM25 searches section text with identifier-aware tokens. It is local, inexpensive and inspectable; a query can miss synonyms or select several sections from one page. No benchmark here establishes that it beats other retrieval methods.

| Alternative | Why consider it | Why it is not the default here |
| --- | --- | --- |
| Dense embeddings | Retrieve paraphrases with little literal overlap. | Adds embedding/index versioning and a dependency; compare fixed-corpus reference recall first. |
| Hybrid lexical + dense retrieval | Combine identifier matches and semantic matches. | Needs a measured fusion strategy and quality/latency comparison. |
| Contextual chunks or reranking | Supply page context or reorder candidate passages. | Additional complexity can improve or worsen retrieval; neither has been benchmarked here. |
| Knowledge graph or specialist agents | Follow relationships or divide distinct tasks. | Existing page links already support bounded navigation. No demonstrated need for a separate graph database or agent team. |

`Corpus.read` returns up to eight validated internal links as page IDs. This is navigation over the stored corpus, not a semantic knowledge graph or permission to browse arbitrary URLs.

## Find the tests by behavior

[Agent tests](../tests/test_agent.py) cover release and permission boundaries; [app tests](../tests/test_app.py) cover once-only work and navigation; [evaluation tests](../tests/test_evaluate.py) cover grading and evidence preservation. The [behavior contract](BEHAVIOR_CONTRACT.md) maps detailed Given/When/Then checks. These establish mechanics; separately versioned real runs measure answer quality.

The historical source-support pilot and optional source-derived coverage experiment predate the task contract. Verification version 2 added frozen question outcomes and typed repair research; version 3 adds workflow facets and read-evidence anchors. The [current repair review](../results/task-completion-repair-v1/review.md) separates measurements by runtime; earlier results cannot establish current behavior.
