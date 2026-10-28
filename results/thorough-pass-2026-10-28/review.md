# October 28 repair review

The pass reproduced an empty overview response, fixed concrete boundary failures, and tested the repaired app at **`ab9a92a`**. The final browser replay delivered six source-checked answers; **five met all task checks**. The overview still omitted Signal completion timing. This review preserves that failure alongside the repairs.

## What was fixed, and why

| Reproduced problem | General correction | Evidence |
| --- | --- | --- |
| Valid grouped citations were rejected; regex parsing disagreed with visible Markdown. | Parse CommonMark after the same normalization as the UI. Every grouped source must still be read and declared; code, links, escaped markers and definitions have explicit rules. | [Captured overview replay](captured-citation-replay.json), [agent tests](../../tests/test_agent.py). Citation contract is now version 3. |
| A formatting failure erased earlier supported recovery facts. | Retain the last eligible proposal, then check its entire narrowed answer again before release. | Accepted and rejected recovery cases in [agent tests](../../tests/test_agent.py). No automatic release of prior claims. |
| The planner repeatedly rewrote missing evidence. | Ask for workflow inputs, timing and outputs; seek a missing premise before resubmitting. | [Intermediate](ui-intermediate/manual-review.json) and [final](ui-final/manual-review.json) answers. The follow-up recovered timing; the overview still failed that check. This instruction does not enforce completeness. |
| Quoted credential values and Basic authorization could leave suffixes exposed. | Mask the whole recognized value, including incomplete quoted input. | [Four offline canaries](credential-sinks.json): no suffix at provider, trace, history or SQLite boundaries; zero network/model calls. This is not general PII detection. |
| Markdown images in questions or answers initiated external requests. | Render image descriptions as text; retain ordinary code and user-initiated links. | Browser fixture [before](markdown-image-before.json) and [after](markdown-image-after.json): three attempted image requests became zero. External attempts were intercepted in both tests. |
| Concurrent reviews lost an entry; typed input could leave a preset queued. | Serialize review read/append/write and consume both input sources once. | [Library](../../tests/test_library.py) and [UI tests](../../tests/test_app.py); live navigation/delivery in [browser receipt](ui-final/browser.json). |
| An earlier failed evaluation turn could be hidden by a successful last turn; recovery ignored a configured judge override. | Aggregate operational errors across every turn and propagate the configured recovery model. | [Evaluation tests](../../tests/test_evaluate.py). Quality failures remain valid completed measurements; infrastructure errors do not. |

The changes are four focused commits: `1f15cf0`, `7a2094d`, `6761be2`, and `ab9a92a`. The final source SHA-256 is `49e53739d78f81fcc69ecb2b48676413c4e3bfa63adf31c133bbf937d8de76d4`.

## Actual browser tasks

The [18 task checks](ui-criteria.json) were written before the first replay. Each run asked the same six questions once: three presets, a dependent follow-up, a made-up API, and actual offline arithmetic plus evaluation guidance. No answer was silently retried. Manual review grades each check separately from the source verifier.

| Version | Fully passed tasks | Task checks | Agent estimate | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Original runtime `3a49a50` | 5/6 | 16/18 | $0.79 | Overview delivered no answer. |
| Boundary repairs `6761be2` | 4/6 | 16/18 | $0.76 | Overview delivered checked partial facts; both it and the follow-up omitted timing. |
| Final runtime `ab9a92a` | 5/6 | 17/18 | $0.90 | Overview explains roles but omits timing; follow-up explains asynchronous completed-turn scoring. |

[Baseline review](ui-before/manual-review.json) · [Intermediate review](ui-intermediate/manual-review.json) · [Final review](ui-final/manual-review.json). These are single development replays, not a controlled estimate of improvement. Initial baseline review mistakenly awarded checks only in whole-case blocks; the retained reviewed record corrects its independent check total to 16/18.

The final answers took **19–57 seconds** (mean 36.8 seconds) and contained **217–428 words**. No speed improvement is claimed. All six saved/rendered once; the follow-up had the actual preceding user/assistant history. Navigation during execution, keyboard access to sources, the analysis link and desktop/mobile layout passed. The arithmetic tool executed and returned 2/4 = 0.5. Generated Weave SDK sketches remain unexecuted.

## Weave readback and monitoring

[Final UI readback](backend-ui.json) reconciles **six turns, 120 spans and 43 model calls**: hierarchy, conversation/source identities, returned usage and estimated costs match the saved answers.

The existing Signal scored all six turns. It incorrectly tagged the arithmetic/evaluation answer as uncited, while its own reason acknowledged a source marker. That is **one false positive among these six selected answers**, not a general precision estimate. The earlier [baseline readback](backend-before.json) includes a correctly tagged exhausted overview and five correct negatives. No Signal policy was retuned during this pass. Signals run after completion and do not block answers.

The exact Signal-worker request remains unavailable through the inspected call-read endpoint. Feedback and its policy version are available. Trace consistency does not prove factual correctness.

## Unchanged regression

**12/13 cases passed; 48/48 factual assertions passed; $2.52 agent + judge estimate.** All 13 predictions completed, with no judge or infrastructure errors. [Summary](../thorough-repair-regression-v1/summary.json) · [Weave evaluation](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving/weave/calls/01a181c5-0a29-7ced-82ac-2598e9053c21) · [All-turn readback](backend-regression.json)

[Case 01](../thorough-repair-regression-v1/cases/01-init--support--t01--7476f567-fb5a-49bb-9a1a-51ba6223705f.json) failed the separate uncertainty threshold. Its answer treated a Verdict integration example as general initialization behavior while acknowledging it lacked confirmation. The source verifier accepted that answer. This illustrates why source checking, assertion grading and overall quality gates remain separate.

The earlier runtime scored 13/13 under the same rubric; this run scored 12/13. One trial of a reused 13-case suite cannot establish a quality gain or regression rate. No rubric or expected-answer change was made to erase the failure. Shared citation integrity parsing changed to contract version 3, so both results retain their runtime identities.

## Reproducibility and limits

- [Local checks](local-checks.json): 310 tests, Ruff, lock and whitespace checks passed. Existing Weave/Pydantic deprecation warnings remain.
- [Fresh clone](fresh-setup.json): exact final commit, frozen dependencies, no credentials or cached pages; all 351 pages/3,569 passages restored with socket access blocked. Runtime imports succeeded and the clone stayed clean.
- [Instrument comparison](instrument-check.json): question, assertion and rubric files and judge logic are unchanged. The shared citation integrity parser changed from version 2 to 3, so the entire evaluation boundary is not byte-identical.
- The corpus remains the October 24 snapshot, reference SDK 0.53.1 versus runtime 0.54.0. No live-document or API-compatibility guarantee was added.
- The original submission tag and completed historical results remain unchanged. Private preparation, credentials and local SQLite data stay outside the public evidence.

The full regression result and its Weave readback are indexed in [results/README.md](../README.md). A source-check pass, a task pass and an online review tag are three different measurements.
