# From the brief to the code

Start with [`Agent.run`](../src/coreweaving/agent.py). It owns one conversational turn: choose tools, gather evidence, submit a draft, check it and repair if needed. The [README](../README.md) covers setup; the [behavior contract](BEHAVIOR_CONTRACT.md) describes the enforced boundaries.

**Validation status:** the simplified implementation uses verification contract 6. The [writer diagnostic](../results/essence-v1/writer-diagnostic/) predates the compact audit report and is inconclusive. Validation of the changed auditor, regression and browser replay follows the [essence protocol](../results/essence-v1/protocol.md); final measurements are pending. The earlier [13/13 regression and 17/18 UI result](../results/product-final-v1/README.md) belong to runtime `dfdb6bd`, not this source.

## Follow one answer

1. [`app.run_question`](../app.py) starts one background job. Streamlit reruns poll real progress and consume its result once. The answer and Sources & analysis live in the current browser session; there is no SQLite answer library.
2. [`Agent.run`](../src/coreweaving/agent.py) sends the question and recent dialogue to the configured writer. The model repeatedly chooses `search_docs`, `read_page`, `run_python` or `submit_answer`. There is no separate task-planning call.
3. `execute` validates tool names and arguments. `Session.add_passage` assigns source IDs only after a read. Search matches, outlines and internal links locate evidence; they do not establish unread content.
4. `verify` applies the Markdown citation contract and Python syntax check. Its auditor receives the original question, retained dialogue, candidate, relevant read passages and research actions. It checks material claims and requested coverage, then returns only `passed`, blocking `issues` and `missing_parts`. A clean audit has no issues; supported claims are not copied into a separate inventory.
5. Rejection goes back to the same writer. The writer can research or revise within the remaining limits. An honest partial answer uses the same checks; there is no terminal judge or extracted-fact recovery path.
6. The result retains the answer, sources, checks, usage and trace identity. Only delivered dialogue enters conversation history. The UI displays the answer and keeps developer detail in Sources & analysis.

Defaults allow ten writer calls, eighteen research dispatches and two repairs. The last writer call permits submission only. A truncated response never executes tools; one fresh retry may use the next existing slot. These limits bound work, not answer quality.

## Files and responsibilities

| File | Role and reason |
| --- | --- |
| [app.py](../app.py) | Streamlit chat, background work and source/analysis display; separates rendering from a running turn. |
| [agent.py](../src/coreweaving/agent.py) | Prompts, typed drafts/verdicts, session evidence, dispatch and the single research/check loop. |
| [corpus.py](../src/coreweaving/corpus.py) | Hash-checked local documents, identifier-aware BM25 and exact passages; no retrieval service or live browsing. |
| [llm.py](../src/coreweaving/llm.py) | Anthropic requests, explicit model spans, caching and returned usage. |
| [config.py](../src/coreweaving/config.py) | Settings, Weave initialization, credential masking and source identity. |
| [telemetry.py](../src/coreweaving/telemetry.py) | Protects reference-shaped literal text on logging copies while preserving real SDK references and dataset-row identity. |
| [sandbox.py](../src/coreweaving/sandbox.py) | Optional bounded Docker execution for offline standard-library Python. |
| [metrics.py](../src/coreweaving/metrics.py) | Counts returned calls and estimates cost, including cached input and rejected attempts. |
| [evaluate.py](../src/coreweaving/evaluate.py) | Frozen datasets, predictions, offline judging, integrity checks and saved run evidence. |
| [budget.py](../src/coreweaving/budget.py) | Evaluation spend reservations/accounting; not an account billing cap. |
| [signals.py](../src/coreweaving/signals.py) | Online monitoring of completed turns and labeled control fixtures. |
| [__main__.py](../src/coreweaving/__main__.py) | Terminal entry point using the same agent. |
| [fetch_docs.py](../scripts/fetch_docs.py) | Offline snapshot restoration or an explicit maintainer refresh. |
| [scripts/experiments](../scripts/experiments/README.md) | Optional historical comparisons and probes, separate from the app path. |

`AGENT_MODEL` selects the writer/researcher; `VERIFIER_MODEL` selects the auditor. Both request medium effort. `JUDGE_MODEL` is used by offline evaluation only, at provider-default effort. The writer remains provisionally configured; the earlier matched diagnostic is inconclusive and does not establish the best model for this changed auditor. See [configuration](../.env.example) for defaults and overrides.

## Three uses of Weave

| Path | What it establishes | Limit |
| --- | --- | --- |
| Conversation → turn → model/tool/verifier spans | What ran, what evidence it read and what it cost. | Trace completeness is not answer correctness. |
| `DocumentationModel.predict` → `QualityJudge.score` | Results against frozen questions, references and assertions. | Reused tasks and same-family models limit independence and generalization. |
| `signals.setup` on `weave.genai.turn_ended` | Post-completion review of this agent's selected ERROR/review-reason turns. | It cannot block answers or detect every factual defect. |

Evaluation references go to the judge, not the agent. Case pass combines assertions, four quality dimensions and deterministic integrity; self-verification and reference overlap are diagnostics. [Evaluation design](EVALUATION_DESIGN.md) explains the suites. Completed local answers and remote delivery are checked separately.

## Decisions and limits

- **Direct loop:** one control flow is easier to inspect than a routing framework or specialist-agent team. No framework comparison was run.
- **BM25:** matches API identifiers and runs locally. An [18-query comparison](../results/retrieval-comparison-v1/README.md) improved selected-evidence recall from 57.0% to 64.4% with hybrid, below the adoption threshold; six live tasks tied on assertions. This supports retaining the baseline, not dismissing semantic retrieval.
- **Separate auditor:** checks support and the actual request without importing every optional page detail. It can miss a claim or omission; its benefit beyond citation checks remains unisolated.
- **Stored corpus:** reproducible evidence from 351 pages, with context and internal links. It is one October 24 snapshot, not a release-aware or current-site search service. [Version limits](VERSIONING.md)
- **Bounded Python:** demonstrates execution without granting host access. Syntax checks and a standard-library container do not validate generated Weave SDK examples.

[Agent tests](../tests/test_agent.py), [app tests](../tests/test_app.py) and [evaluation tests](../tests/test_evaluate.py) protect behavior. The [five auditor controls](../results/essence-v1/auditor-controls.json) test acceptance of supported answers as well as rejection of false claims and requested omissions. Live runs measure usefulness, latency and delivery; a verified flag is not a quality score. The [build log](AI_BUILD_LOG.md) explains why the earlier planning, workflow and recovery machinery was removed.
