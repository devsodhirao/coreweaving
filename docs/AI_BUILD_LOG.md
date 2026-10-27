# AI build log

Codex implemented the application, tests, evaluation and documentation, with bounded support agents for research and review. Claude's desktop session helped with account setup and project visibility. The owner directed the product priorities, reviewed failures and called for scope reduction.

**The work exceeded the brief's three-hour budget.** The core assistant, tracing, Signals and evaluation landed in the first session; comparison experiments, browser investigation and repairs followed. Commit timestamps mark milestones, not hands-on duration. [Git history](https://github.com/devsodhirao/coreweaving/commits/main/) preserves the full record.

## Timeline and current result

| Stage | Outcome |
| --- | --- |
| October 25: initial implementation | Direct tool loop, source checking, multi-turn context, Weave integration and evaluation. |
| October 25–26: comparison | Six capability questions, two repeats, three verification policies. Coverage checking refused answerable tasks; support stayed the default. |
| October 26: submission and repairs | Tagged runtime `755036e` scored 10/13, 45/48. Clean-install and real-browser checks exposed failures beyond the local tests. |
| October 27 UTC: final review | Runtime `3a49a50` scored **13/13, 48/48** under rubric 2.3. Four UI journeys passed 12/12 checks. These are development results; the original submission evidence is unchanged. |

[Final regression](../results/brief-final-regression-v1/summary.json) · [Versioned comparison](../results/brief-e2e-v1/comparison.json) · [Browser review](../results/brief-e2e-v1/ui-final/manual-review.json)

## What went wrong, what changed, what supports it

| Failure or mistaken assumption | Correction or decision | Evidence and remaining boundary |
| --- | --- | --- |
| Upstream documentation changed, breaking a hash-locked clean install. | Bundle the licensed snapshot; validate archive and page hashes during offline restoration. | [Fresh clone](../results/brief-e2e-v1/fresh-setup-final.json): 351 pages restored without cached documents or credentials. |
| Redaction passed plain-list tests but crashed on WeaveList dataset rows; the evaluation exited successfully with no predictions. | Normalize SDK containers, test their actual types and fail incomplete runs. | [Original failure](../results/readiness-head-20261026-v1/summary.json): zero predictions and model calls, not a 0/13 quality score. |
| Naive section splitting broke code fences; redirected URLs collided; later passages lost page warnings. | Respect fences, distinguish indexed/canonical identity and carry page context. | [Structure check](../results/submission-repair-v1/corpus-structure-check.json), [corpus code](../src/coreweaving/corpus.py). Passage length limits can still truncate examples. |
| Malformed or undeclared citations escaped incomplete checks; inline `[S1]:` punctuation was later rejected incorrectly. | Share a bounded Markdown-aware citation contract across release and evaluation; retain matching-source checks. | [Citation replay](../results/coverage-pilot-v1/citation-replay-v2.1.json), [preset investigation](../results/preset-check-summary.json). Syntax and source identity do not establish factual support. |
| Forced tool choice failed; native instrumentation duplicated explicit agent spans. Cache accounting could show negative displayed costs. | Validate ordinary tool responses, disable duplicate instrumentation and normalize usage for Weave while preserving provider categories. | [Adapter](../src/coreweaving/llm.py), [final backend readback](../results/brief-e2e-v1/backend-final.json). Costs remain estimates from returned usage. |
| Streamlit reruns interrupted research; repeated question labels selected the wrong saved answer. | Run and persist work independently of rendering; consume completion once and use stable record labels. | [Navigation check](../results/ui-recovery-v1/browser.json), [selection reproduction](../results/final-readonly-ui.json). Process restart can still lose unfinished work. |
| Generated examples dropped assistant replies, then accepted tool results without preceding assistant tool calls. | State the general history invariant; preserve assistant tool-use blocks and matching result IDs. | [Captured failure](../results/brief-e2e-v1/ui-repair/tracing-history-reproduction.json), [final stub replay](../results/brief-e2e-v1/ui-final/tracing-history-reproduction.json). Generated SDK integrations were not run against live APIs. |
| Extra verification rejected useful answers and ordinary deductions. | Keep support checking as default; distinguish support from coverage and allow deductions from explicit premises. Retain bounded recovery and negative checks. | [Pilot](../results/coverage-pilot-v1/summary.json): support and off tied on 39/44 factual assertions. No citation-only arm isolated the model auditor's value. |
| Multi-concept searches missed a premise; repairs removed requested outcomes. | Research each requested outcome with focused queries and preserve the direct answer during repair. | [Baseline cases 05/11](../results/brief-e2e-v1/baseline-review.json), [final answers](../results/brief-e2e-v1/final-answer-review.json). BM25 stayed unchanged; this is no retrieval-model comparison. |
| Case 03 demanded optional Signal controls and an unsolicited disclaimer. | Correct two assertions in rubric 2.3; retain questions, references, the other 46 assertions and old scores. | [Fairness review](EVALUATION_DESIGN.md), [comparison](../results/brief-e2e-v1/comparison.json): common assertions improved from 43/46 to 46/46. Case 03's new pass is not evidence of a runtime repair. |
| A positive verifier fixture lacked the editing evidence its question required. | Correct the fixture and rerun both policies; preserve the confounded first probe. | [Fixture review](../results/brief-e2e-v1/verifier-fixture-review.json): corrected old/new policies tied 6/6. [Seven final selected probes](../results/brief-verifier-final-v1/scope-correction.json) matched labels; neither estimates population accuracy. |
| The legacy monitor did not score agent turns; the later Signal flagged 14 of 15 normal baseline turns. | Use the current turn-ended contract and agent filter; define exactly three review conditions with exclusions and evidence. | [Diagnosis](../results/brief-e2e-v1/signal-diagnosis.json): all 14 tags were false positives under its policy. [Six fixtures](../results/brief-e2e-v1/signal-calibration/summary.json) matched; [15 final turns](../results/brief-e2e-v1/signal-final-review.json) correctly received no tag. Broad precision/recall remains unmeasured. |
| A green source check concealed incomplete answers and invalid examples. | Review delivered answers and browser journeys separately from source support. Preserve disagreement with the judge. | [Answer audit](../results/brief-e2e-v1/final-answer-review.json): case 02's hierarchy pass is generous. [UI review](../results/brief-e2e-v1/ui-final/manual-review.json): answers still took 23–45 seconds and 340–383 words. |

## What the evidence supports

The project demonstrates a bounded, inspectable documentation agent and a measurement process that found real failures. The final 13 questions were reused during development, the verifier and judge share a model family, and a source-check pass can still be wrong. [Evaluation design](EVALUATION_DESIGN.md) separates those limitations from the recorded outcomes.

Weave provides agent traces, evaluation records and online feedback. Anthropic runs the assistant and offline judge; CoreWeave Serverless Inference runs the Signal. We did not train a model or host the app on CoreWeave GPUs.

Voice, adaptive interfaces, graph retrieval and additional specialist agents remain deferred. The implementation already exceeds the original time budget; latency, brevity and scope are still tradeoffs to explain. [Code map](CODE_MAP.md) · [Evidence index](../results/README.md)
