# Retrieval comparison: protocol frozen before rankings

Question: does a small contextual or hybrid search change help this assistant find
the necessary evidence earlier, while preserving precise API matching?

## Fixed basis and arms

- App basis: `a628da0`; runtime fingerprint and snapshot are recorded by the runner.
- Runtime, prompts, support verifier, tool schemas, source reads and citation rules
  stay unchanged. Only an experimental `Corpus.search` implementation varies.
- **Baseline:** the existing BM25 implementation, including title/heading weighting.
- **Contextual:** the same lexical approach with bounded source-derived introductory
  prose and ancestor headings. No generated context or query-specific annotations.
- **Hybrid:** contextual lexical candidates plus local BGE-small-en-v1.5 semantic
  candidates, combined with reciprocal rank fusion (`k=60`). Exact model revision,
  windowing, candidate depth and context rules are frozen in the backend receipt.
- Same result budget: six passages, maximum two per page. Eight is secondary only.
  Search snippets remain navigation; only original reads can support citations.

The source author prepares 18 new queries in nine information-need families,
covering paraphrases, exact APIs and cross-page workflows, without running search.
Each required fact has a quoted reference section and any identified alternatives.
A separate reviewer checks question validity and reference sufficiency. Freeze the
dataset hash and backend configuration before observing any ranking. This is a
prospective probe, not a permanently held-out benchmark or an exhaustive relevance set.

## Offline measures and selection

Primary: mean fraction of required evidence nuggets found in the first six results
and fraction of questions whose every nugget was found. Count a nugget once when
any predeclared acceptable section is returned. Report category and family results,
first relevant rank, exact identities, query latency and index build size/time.
References are selected evidence, so alternative valid hits can be reviewed after
the run, but they do not replace the original frozen scores.

Choose the alternative with the highest mean nugget recall@6, breaking ties by
all-nugget coverage and then preferring contextual lexical search. Do not retune
weights, windows or references after seeing results. A gain of at least 0.10 in
mean nugget recall, with no decrease in exact-API all-nugget coverage, is the
predeclared meaningful offline improvement. Smaller or mixed gains remain findings.

## Paired agent check

Run baseline and the selected alternative on six preselected queries (two per
category, distinct information-need families). Select by ID within category,
skipping previously selected families, in category order paraphrase, exact API,
workflow. Alternate baseline-first and candidate-first order across pairs. One
trial each: 12 fresh sessions. Selection is fixed before rankings, not based on
which queries favor the candidate.

Use the existing unchanged assertion judge and support-mode runtime. The judge
sees the question, assertions, reference passages and answer, not the arm label.
Keep models, unspecified provider effort, caching, limits and rubric fixed. Use
one shared $5 estimated agent-plus-judge budget with conservative reservations;
no retries after provider/budget failure and no cherry-picked replacement cases.
Preserve incomplete cells and report matched pairs separately. Signals and costs
without returned usage are outside this estimate.

Report per-case assertion/quality results, manually reviewed regressions, searched
and read sections, planner/verifier calls, engine latency, query latency and cost.
The first loaded index is prepared before agent timing; report cold preparation
separately. Cache usage and paired order are recorded because they affect timing.
Use Weave agent traces and Evaluation records, and distinguish local completion
from remotely delivered records.

## Adoption rule

Keep the current default unless the meaningful offline threshold is met and the
paired agent check shows no lost assertion or material manual-review regression,
plus either a quality improvement or at least 20% lower median engine latency.
An incomplete comparison cannot qualify. Even a qualifying result is a small
pilot: before changing the default, run the unchanged regression and capability
suites on the proposed implementation, with a separately recorded run budget.
Do not represent an offline retrieval gain as a measured answer-quality gain.

No voice, graphs, specialist agents, model changes, reranker or live-web retrieval
is added in this experiment. Original results and submission tag stay intact.
