# Hybrid follow-up: promising evidence, answer benefit still unmeasured

**Hybrid improved discovery on two fresh wordings; it tied on four.** Keeping
BM25 provisionally is reasonable, but the earlier pilot did not establish that
hybrid has no benefit. This follow-up made no app changes and no paid calls.

## What was missing from the earlier test

The original hybrid gained on three queries that were absent from its six-task
live comparison. The live judge also missed code and citation defects. Its
14/14 tie cannot resolve whether those retrieval gains would help users.

The old frozen ten-point adoption threshold was a complexity trade-off, not a
statistical significance test. At eight results, original BM25 recall rose from
57.0% to 61.7%; hybrid stayed at 64.4%. That suggested a cheaper alternative worth
checking alongside hybrid. [Original records](../retrieval-comparison-v1/README.md)

## Current-runtime offline check

Six fresh questions cover three earlier gains, one earlier loss and two exact-API
controls. They share five information needs. We froze their wording and reviewed
source quotes before rankings; the answer assertions are inherited unchanged.
One known valid application-version source was added before this new run.
These are targeted development cases, not a representative or held-out sample.

The app runtime remains `522c320`, source `bd74bb83b9fd...`, using the same 351-page
snapshot. Hybrid uses the original local BGE-small model and fixed rank fusion.
The cached vectors were reused only after matching text, ordered windows, owners,
encoder identity, checksum and shape. [Protocol](protocol.md) · [Cases](cases.json)
· [Exact identities](freeze.json) · [Rankings](offline.json)

| Freshly worded task | BM25, 6 results | BM25, 8 results | Hybrid, 6 results |
| --- | ---: | ---: | ---: |
| Retrieve a fixed older prompt | 0/2 facts | 0/2 | **1/2** |
| Version an app and compare individual answers | 1/2 | 1/2 | 1/2 |
| Display existing images in ordinary and agent traces | 1/3 | 1/3 | 1/3 |
| Configure existing screenshot storage | 1/3 | 1/3 | **2/3** |
| Exact API: Op postprocessing | 3/3 | 3/3 | 3/3 |
| Exact API: daily Call metrics | 3/3 | 3/3 | 3/3 |
| Mean selected-source recall | **52.8%** | **52.8%** | **66.7%** |

These numbers count predeclared supporting sections in one search. They are not
answer accuracy. All three configurations found every selected section for only
the two exact-API controls. The aggregate is intentionally enriched for previous
retrieval problems and cannot be compared directly with the original 18-query
average. [Validation](validation.json)

## What the differences mean

- **Prompt versioning is the clearest navigation benefit.** Hybrid reaches the
  prompt-versioning page; neither keyword budget does. The pinned-reference
  section is still absent, but reading the page exposes an outline for locating it.
- **Application versioning is a tie.** Keyword search already finds a valid
  alternative explanation of application versions. Neither method locates the
  selected per-example comparison instructions in this query.
- **Media is also a section-selection problem.** Both methods reach the needed
  pages, but neither returns the Op/agent logging sections for the workflow
  wording. On the setup wording, hybrid additionally surfaces bucket registration;
  explicit access/CORS instructions remain missing. Reaching a page and reading
  its relevant section are different achievements.
- **The old loss reverses under different wording.** Hybrid lost the registration
  section in the original screenshot question but gains it here. That is a reason
  to test wording robustness, not choose whichever wording favors one method.
- **More keyword results are not a universal fix.** Eight results add no selected
  evidence here and return more text. No end-to-end token or latency claim follows.

## Why single-query recall understates the agent

On the six *historical* keyword-agent tasks, the original raw-question searches
found **71.1%** of selected sources on average. The union of actual agent searches
found **80.0%**, and actual passage reads covered **96.7%**. The agent can reformulate
queries and read additional sections after reaching a page.

Those are descriptive measurements of different evidence budgets, not a controlled
effect of rewriting, not current-runtime accuracy, and not the six fresh questions
above. They explain why improving a raw-question search may leave final answers
unchanged. [Saved-record reanalysis](historical-reanalysis.json)

## Decision and next comparison

**Keep the current default while retaining hybrid as a credible candidate.**
The most useful next experiment is whether the fresh prompt-versioning and setup
gains reduce research rounds or repair an answer, while preserving the workflow
and exact-API controls. Use the same six frozen questions for both methods on the
current agent, with three paired attempts per question and alternating order.

Review task fulfillment, source attribution, omitted prerequisites and generated
code separately from the judge's score. Record all attempts, planner calls, cost
and engine time; UI time requires an actual browser measurement. A repeated
targeted gain would justify a broader regression check, not immediate adoption or
a claim of general superiority. No live follow-up has been started or budgeted.

The original selected cases should remain available as wording-regression
controls if the candidate progresses. Broader claims need new information needs;
fresh paraphrases of these known cases remain development evidence.

Reproduce the offline probe using the command in [replay.py](replay.py), in a
separate checkout/output directory with the original local model/cache available.
Completed receipts are never overwritten. Production code, dependencies, original
scores and the submission tag are unchanged.
