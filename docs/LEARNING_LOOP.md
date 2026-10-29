# How the evidence improves the product

The useful outcome is a developer completing a documentation task with supported guidance and an acceptable wait. Traces, tests and reviews help only when they expose a cause, change a decision and support a subsequent check. They are not the product's purpose.

## Decisions the records changed

| Observation | Decision | What the evidence establishes |
| --- | --- | --- |
| A source-supported overview omitted part of the request. | Give the auditor the original question and assess requested completeness as well as claim support. | Supported fragments can still leave a task unfinished. [Captured failure](../results/thorough-pass-2026-10-28/ui-final/01-overview.json) |
| Rich outcome/quotation schemas caused truncation and rejected useful drafts because the auditor paraphrased its own report. | Remove the separate planning/facet/recovery paths and positive-claim inventory; report problems through one bounded loop. | A report-format check was blocking valid content. The [first compact-audit controls](../results/essence-v1/auditor-check-v1/semantic-review.json) accept two useful answers and reject three substantive defects; broader validation is recorded in the [current packet](../results/essence-v2/README.md). |
| A Signal classifier called a cited answer uncited. | Move eligibility into a server filter over recorded runtime reasons; use the model to explain selected turns. | Eligible/excluded fixtures test the filter and worker path, not broad correctness detection. [Current policy and attributed history](../results/product-final-v1/signal-readback.json) |
| Hybrid improved retrieval, but the live comparison excluded its gain queries. Fresh wordings again show selective gains. | Keep BM25 provisionally; test whether the gained evidence helps actual answers. | A missing answer-quality measurement is not evidence of no benefit. [Original](../results/retrieval-comparison-v1/README.md) · [Follow-up](../results/retrieval-followup-v2/README.md) |
| Plain-list tests passed but real Weave containers crashed evaluation. | Test the actual SDK boundary and treat zero predictions as infrastructure failure. | Fake fixtures cannot establish integration compatibility. [Build log](AI_BUILD_LOG.md) |
| An evaluation parent arrived while child rows were missing. | Read back expected rows, Agent roots and provider usage separately. | Local success and a matching aggregate do not prove complete remote delivery. [Preserved diagnostic](../results/task-completion-repair-v1/backend-retry-missing-rows-diagnostic.json) |
| An overview confused the conversation shown in the UI with the turn that Signals score; an initialization answer omitted authentication. | Add general subject/action/target guidance and setup-context reading, then preserve both real turns and minimally corrected controls. | The [four controls](../results/essence-v2/auditor-check/semantic-review.json) did not establish the intended repair: neither targeted defect was identified in the rejection reasons. More specific instructions alone did not make the auditor dependable. |
| A browser timer counted progress text and could stop before code appeared. | Exclude progress; record terminal prose and populated-code render readiness separately, then compare DOM code with the exported answer. | [Unpaid observer checks](../results/essence-v2/render-measurement-proof.json) verify the clock logic; actual replay still measures product behavior. |
| One-off judge calls wrote cache tokens without reading them. | Disable judge caching; retain useful conversation caching. | Returned usage justified a specific cost correction. [Current evaluation implementation](../src/coreweaving/evaluate.py) |

The latest simplification preserves failures, questions, references and rubric 2.3. The [writer diagnostic](../results/essence-v1/writer-diagnostic/review.json) belongs to the preceding audit contract; it cannot prove the revised auditor's speed or accuracy. Current runtime measurements belong to the [essence packet](../results/essence-v2/README.md).

## Is this reinforcement learning?

No model weights or learned policy are updated. This is an engineering feedback loop: preserve a failure, inspect its cause, curate a test, change code or instructions, then measure again. Reviews do not automatically become trusted documentation or user memory. Calling it reinforcement learning would overstate the implementation.

A useful future memory boundary is explicit curation: a person reviews the question, source evidence and expected answer before adding it to an evaluation dataset. A new conversation does not silently reload a person's earlier chats. [Memory ownership](BEHAVIOR_CONTRACT.md#memory-ownership)

## How to avoid fooling ourselves

1. Preserve first attempts, including refusals, partial answers, timeouts and missing records.
2. Test a legitimate positive alongside the targeted negative. A stricter verifier that blocks useful answers can make the product worse.
3. Check delivery before interpreting semantics: a truncated verdict is not a correctly identified factual error.
4. Score the user's request, not every optional detail in a documentation page. Preserve and explain any justified rubric correction.
5. Separate task completion, source support, code validity, trace delivery, cost and visible latency. A green status does not combine them into truth.
6. Keep development and held-out evidence distinct. Once a failure informs a fix, that example is development data. The existing 13-case regression is such a set.

## Next measurements worth making

| Question | Smallest useful test |
| --- | --- |
| Does model auditing earn its cost beyond citation checks? | Compare citation-only and citation-plus-auditor on new answerable positives and misleading negatives, with independent review of false acceptance, false refusal and completion. |
| Where does the remaining wait occur? | Separate research calls, audit/repair calls and engine-end-to-visible delay. Change one bottleneck at a time; keep task quality fixed. |
| Does the same-family judge miss shared mistakes? | Have an independent reviewer label stored answers before seeing model grades; report disagreements by assertion, not merely an average score. |

Current agent and auditor calls explicitly request medium effort; the offline judge uses provider-default effort. The initial task-planning call has been removed. `app.run_question` still waits for trace flushing before returning, so visible time can exceed agent time. These are current facts; older latency profiles describe their original runtimes.

The right use of the evidence is sometimes to remove a check or decline a feature. More agents, graphs, traces or passing development tests are not improvement by themselves.
