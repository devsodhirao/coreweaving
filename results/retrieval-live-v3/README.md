# Hybrid improved first-search recall; this agent comparison tied on task outcomes

**Keep BM25 for the current presentation.** Hybrid remains a credible candidate,
but this run did not meet the frozen rule for advancing it: no repeated answer
improvement, no reduction in searches overall, and mixed time/cost results.
This is a decision for this app and these tasks, not evidence that hybrid search
is generally unnecessary.

We tested the six existing questions that the offline follow-up had identified,
including its two retrieval-gain wordings and two exact-API controls. Each method
answered each question twice: **24 answers, 12 paired comparisons** on current
source `b312a2c9a081`. Both methods used the same current writer/checker, source
snapshot, six-hit limit, assertions and reference-based judge. Arm order alternated
and reversed for the second repeat. The questions cover five known information
needs; they are development cases, not held-out tasks. [Frozen protocol](protocol.md)
· [Exact identities and order](freeze.json) · [Questions](../retrieval-followup-v2/cases.json)

## What happened

| Measure | Current BM25 | Existing hybrid |
| --- | ---: | ---: |
| Judge-recorded task passes | 12/12 | 12/12 |
| Judge-recorded assertions | 28/28 | 28/28 |
| Tasks supported in AI-assisted source review | 12/12 | 12/12 |
| Searches across the 12 answers | 20 | 20 |
| Document-section reads | 61 | 63 |
| Provider requests, including answer checks | 70 | 70 |
| Model audits | 16 | 16 |
| Median engine time | 26.46 s | 25.80 s |
| Mean engine time | 30.30 s | 29.43 s |
| Estimated answer-generation cost | $2.6568 | $2.8940 |

Hybrid was faster in **6/12 pairs** and slower in six. It cost less in **7/12
pairs**, but its total answer-generation cost was about **8.9% higher**. Both
methods made the same number of searches in every pair. Small median differences
and isolated wins do not establish a reliable speed or cost advantage.
[All paired measurements, queries and review notes](comparison.json)

| Task | BM25 seconds, repeats 1 / 2 | Hybrid seconds, repeats 1 / 2 | BM25 cost, both answers | Hybrid cost, both answers |
| --- | ---: | ---: | ---: | ---: |
| Pin Friday's prompt version | 23.38 / 28.05 | 25.76 / 23.72 | $0.338 | $0.309 |
| Compare application revisions | 22.80 / 25.68 | 44.89 / 22.79 | $0.519 | $0.725 |
| Images in ordinary and agent traces | 24.76 / 41.27 | 25.84 / 26.13 | $0.542 | $0.470 |
| Existing screenshot storage setup | 27.24 / 28.64 | 30.04 / 46.79 | $0.460 | $0.611 |
| Exact API: Op postprocessing | 54.82 / 39.67 | 24.46 / 42.45 | $0.507 | $0.493 |
| Exact API: daily call statistics | 22.52 / 24.80 | 19.69 / 20.54 | $0.292 | $0.286 |

Times are full agent engine times, including research and checks, excluding the
separate evaluation judge, setup and browser rendering. Costs use provider-returned
usage and the saved price table; they exclude local CPU, Signals, hosting and taxes.
Caching stayed enabled for both agents. The two methods wrote different amounts
to the provider cache, so this is observed application cost, not an isolated
retrieval-computation price or a prediction of another session's bill.

## Why the offline gain did not become an answer gain here

The offline probe searched the user's raw sentence once. The agent chose shorter
queries and read more sections. For Friday's wording, **all four attempts searched
`retrieve specific prompt version ref`**. Both methods reached the relevant page
and loaded the pinned-reference instructions. For screenshot setup, every attempt
made two searches and read six or seven sections, including permission, CORS and
registration instructions. This is a supported explanation of these records,
not a controlled estimate of the benefit of query rewriting.

The earlier offline result remains valid: selected-source recall was 52.8% versus
66.7%, with two gains and four ties on these wordings. That metric counts selected
sections returned by one search; it does not measure final-answer correctness.
[Offline comparison and its limitations](../retrieval-followup-v2/README.md)

## What a pass still missed

Source review found no material failure of the frozen requested tasks, but it
recorded minor overstatements: some image answers omitted supported videos when
describing other formats, and prompt-version answers loosely described every
publish as a new version without the changed-content condition. Some answers were
long or used deliberately incomplete SDK scaffolds. No SDK/storage examples were
executed. Correct Python syntax is not compatibility evidence.

The shuffled review packets hid method, cost, time and grade. The reviewer was the
coding assistant, had seen operational logs and some grades, and had already seen
one answer with its method known. Verdicts were saved before the label keys were
opened. This is **partially blinded AI-assisted review**, not independent human
calibration. The writer, checker and automatic judge also share a model family.
There were no task-pass disagreements with the judge; the wording concerns remain
visible rather than turning those passes into a claim of perfect accuracy.
[First review](review-verdicts-1.json) · [Second review](review-verdicts-2.json)

All **124 read-section occurrences** matched the snapshot hashes and expected
stored text. Four had documented credential masking of public documentation
examples; they were not byte-identical to the raw section. Citation identity and
Python syntax checks reported no issues. These checks establish source identity
and structure, not the truth of every sentence. [Checks](comparison.json)

## Preserved operational failure and accounting

The original run stopped after the fifth answer because its judge returned prose
instead of the required `record_grade` call. That is an invalid grade, even though
the prose said the answer passed. The response was delivered and its usage was
known. We preserved the answer, invalid score and incomplete original summary.
A disclosed resumption retried only that grade with the same answer and contract,
then ran the untouched remaining plan. No quality failure was retried.

The first resumption preflight failed before model calls because an in-memory tuple
was compared with its JSON list representation. The follow-up changed only that
comparison's normalization; the original script and preflight receipt remain.
[Original summary](summary.json) · [Resumption policy](resumption.md)
· [Preflight record](preflight/receipt.json) · [Completion view](completion.json)

**Total estimated model cost: $7.6281**, within the $20 allowance: $5.5508 for the
24 answers and $2.0773 for **25 judge requests**, including the invalid grade.
Remote readback verified all **24 turns, 140 agent responses and 25 judge
responses**, including exact saved outputs, parentage and returned usage. This is
a paired agent experiment using the existing judge, not a new `weave.Evaluation`
parent or a replacement for the brief's full regression. [Readback](backend-readback.json)

## Engineering decision and remaining limits

Hybrid combines contextual BM25 with pinned BGE-small embeddings and equal
reciprocal-rank fusion. It changes both context and semantic retrieval, so this
comparison does not isolate embeddings alone. It adds a 66.5 MB local ONNX model,
a 6.23 MB compressed vector cache, encoder dependencies and rebuild/version checks.
Initial preparation with existing vectors took 7.10 seconds for hybrid and 1.54
seconds for BM25; these are one warm-cache observation each, not cold-install
benchmarks. Recorded search-tool spans had medians of 7.9 ms for BM25 and 16.4 ms
for hybrid (20 searches each; totals 0.16 and 0.45 seconds). These include tool
adapter work, not just ranking. Retrieval computation was a small part of these
agent waits. [Search-span timings](search-timings.json) The model's weight hash matches the official file; the exact upstream
revision association of its mirrored configuration files remains partly inferred,
as disclosed in the original provenance record in `freeze.json`.

The user's preference for hybrid is reasonable. A decision to use it could be
framed as accepting extra setup for broader semantic matching; it cannot be framed
as a measured answer improvement from this run. For a presentation with an already
working default, the added deployment work is not earned by these results. Keep
the existing candidate available. Revisit it if new information needs or observed
paraphrase failures expose repeated answer or research-cost gains. Do not add more
repeats to this familiar all-pass set merely to seek a favorable result.

The next engineering priority is the expensive checker and concrete answer
omissions, not a new retrieval service. This experiment leaves the runtime,
dependencies and production BM25 default unchanged.

## Reproduction

`run.py` freezes settings and verifies the prior raw-query rankings before paid
calls. `resume.py` documents the one operational resumption. `assemble.py` computes
paired results from saved records after source review. Each refuses to overwrite
completed output. Reproduction needs a fresh output location, the exact licensed
snapshot and prior pinned local model/vector files, and explicit model spending.
The experimental dependency was `fastembed==0.9.1`; it was supplied through `uv
--with`, not added to the app's lockfile. No new monitor was activated.
