# Does hybrid retrieval earn its complexity?

**Decision: keep BM25 as the app default.** Hybrid found more selected evidence,
but missed the improvement threshold set before results. On six paired agent
tasks it produced no additional passing assertions and saved only one model call
overall. The implementation stays in optional experiment scripts; app code,
dependencies, prompts, verification and the original regression results are unchanged.

## What we compared

| Arm | Change from the existing search |
| --- | --- |
| BM25 | Existing identifier-aware lexical search. |
| Contextual BM25 | Add bounded introductory prose and ancestor headings from the source page. No generated summaries. |
| Hybrid | Fuse contextual BM25 and local BGE-small semantic rankings with equal-weight reciprocal rank fusion, `k=60`. |

All arms use the same snapshot, six search results, two results per page and
original evidence reads. The hybrid model is a pinned, quantized ONNX export;
long sections use overlapping token windows. No vector service is involved.
[Implementation and reproduction](../../scripts/experiments/README.md)

We froze **18 new queries in nine paired families**, their evidence nuggets and
six live tasks before inspecting rankings. Independent review corrected two unfair
assertions before the freeze. The adoption rule required at least a **10-point
recall gain**, preserved exact-API coverage and a subsequent answer-quality or
20% latency improvement without regressions. [Protocol](protocol.md) ·
[Instrument review](instrument-review.json) · [Frozen identities](freeze.json)

## Offline retrieval

Recall is the mean fraction of each query's preselected evidence nuggets found
in its first six results. It is not answer accuracy.

| Search | Nugget recall@6 | All nuggets found | Median search time |
| --- | ---: | ---: | ---: |
| BM25 | 57.0% | 7/18 | 10.4 ms |
| Contextual BM25 | 57.0% | 7/18 | 11.6 ms |
| Hybrid | 64.4% | 7/18 | 24.5 ms |

Hybrid's **7.4-point gain** came from three queries: pinned prompt versions,
application versioning and media logging. It lost the bucket-registration passage
for another question. Exact-API recall stayed 94.4%; plain-language recall rose
from 50.0% to 61.1%. Contextual BM25 had no aggregate gain.
[Scores and rankings](offline.json) · [Independent interpretation](offline-review.json)

Cold preparation took **0.8 s / 1.5 s / 345.7 s** for baseline/contextual/hybrid.
Hybrid added a 66.5 MB model and 6.9 MB of vectors across 4,494 windows. The paired
agent run reused that index; cold setup is excluded from engine timings.
[Model provisioning](model-provisioning.json) · [Official-file verification after connectivity recovered](official-model-readback.json)

## Paired agent results

The six tasks were selected before rankings, with alternating arm order and one
trial per arm. Both use the existing support verifier and unchanged LLM judge.

| Recorded result | BM25 | Hybrid |
| --- | ---: | ---: |
| Judge-passed tasks | 6/6 | 6/6 |
| Passed assertions | 14/14 | 14/14 |
| Total agent model calls | 36 | 35 |
| Planning calls, including task plans | 29 | 28 |
| Verifier calls | 7 | 7 |
| Median engine time | 28.42 s | 24.78 s |
| Agent + judge estimate | $1.16 | $1.28 |

| Task | BM25 time / calls | Hybrid time / calls |
| --- | ---: | ---: |
| Remove private function data from traces | 23.48 s / 5 | 18.72 s / 5 |
| Daily metrics without downloading every call | 26.23 s / 5 | 41.18 s / 7 |
| Pin a prompt reference | 39.92 s / 8 | 18.57 s / 5 |
| Log historical conversation batches | 19.51 s / 5 | 19.77 s / 5 |
| Expert review to evaluation dataset | 30.61 s / 6 | 33.75 s / 7 |
| Version an application and compare evaluations | 36.53 s / 7 | 29.79 s / 6 |

Total: **$2.44 across 83 agent and judge calls**, within the shared $5 estimate
budget. Hybrid's observed median was 12.8% lower, below the 20% threshold. With
one trial, provider variation, cache reuse and repair differences prevent a causal
speed claim. Its largest apparent speed gain coincided with the verifier accepting
a citation attribution that the baseline verifier required repairing.
[Recomputed totals](live-comparison.json) · [Original local run](live/summary.json) ·
[Independent answer review](live-review.json)

## Why passing scores are not enough

- **Invalid Python in both arms:** credential masking consumed a parameter type
  annotation in the postprocessing example. The explanation satisfied its assertions,
  but the emitted code failed Python parsing. A correct source and a passing judge
  did not guarantee usable code.
- **Uneven source checking:** hybrid's prompt-reference answer attributed the URI
  shape to a passage lacking it. The needed passage had been read, but the attached
  citation was wrong; the evaluation judge noted the issue but still passed it.
  Hybrid also unnecessarily doubted whether expert labels
  transfer into the dataset despite explicit source support. Both daily-metrics
  examples need valid date bounds before execution.
- **Trace export failure:** ordinary search text beginning `weave:///` was treated
  as a reference and rejected with HTTP 400. All answers and scores are saved locally;
  only 10/12 Agent traces arrived, and Weave's parent aggregation failed. The
  original local summary's `complete` means all 12 local score records exist;
  its `weave_summary` is null. The stalled post-run flush was terminated after
  preserving the records. [Process receipt](run-lifecycle.json) · [Exact readback](backend-readback.json) ·
  [SDK diagnosis and offline reproduction](export-diagnosis.json) ·
  [Weave evaluation](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/r/call/01a184ec-63b6-73ef-bc86-db86063776a3)

These are concrete repair candidates, not evidence for switching search methods.
The tracing remedy must preserve literal telemetry text without changing the
queries, passages or evidence the agent actually used.

## Limits and next decision

The 18 queries share nine information needs. Curated references omit some valid
alternatives; four queries cannot expose every selected nugget in one search under
the two-hits-per-page cap. The agent can re-query or read more sections. The six
preselected live tasks do not include the three offline gain queries, so this check
does not establish whether those gains would improve answers. A post-hoc exact-quote
exposure diagnostic is preserved in the offline review and does not replace the
frozen metric. The same-family judge missed defects found during manual review.

This compares one small embedding model and one fusion configuration. It does not
test dense-only search, learned routing, reranking or LLM-generated contextual
chunks. [Anthropic's contextual retrieval](https://www.anthropic.com/research/contextual-retrieval)
is a different context-generation procedure; its published gains are not our result.

Repair code delivery and trace serialization first. Any later retrieval change
needs a new frozen task set, repeated paired runs and a gain that outweighs setup
cost. [513 local tests and checks](local-checks.json) cover experiment boundaries;
they do not certify the generated answers.
