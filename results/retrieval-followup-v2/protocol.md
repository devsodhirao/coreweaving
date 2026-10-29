# Retrieval follow-up: inspect the missing link

This is an offline diagnostic on the current runtime, not a new answer-quality
evaluation. No generative API calls, default changes or paid runs are included.
The earlier experiment and its adoption rule remain unchanged.

## Question

Does the earlier hybrid gain survive different wording, and does allowing two
more keyword-search results offer a simpler way to expose the same evidence?

## Freeze before rankings

- Six new wordings reuse known information needs and reviewed source references.
  Three target earlier hybrid gains, one targets its setup-detail loss, and two
  retain exact-API controls. These are selected development diagnostics, not six
  independent new user needs or a held-out sample; the two media cases share a
  family. Report targeted cases and controls separately.
- `cases.json` contains the questions, unchanged answer assertions, literal
  evidence quotes and any declared alternative source. An existing alternative
  application-version passage is added before this run; old scores are untouched.
- Compare current BM25 at six results, current BM25 at eight, and the existing
  frozen hybrid algorithm at six. The two-results-per-page cap stays fixed.
  The larger keyword result budget is an alternative configuration, not an
  equal-context ranking comparison.
- Record runtime, corpus, dataset, experiment source and model identities before
  searching. The current source is `522c320` / `bd74bb83b9fd...`.
- Reuse existing vectors only if the indexed text, ordered windows, owners and
  complete embedding identity match the old receipt, and the cache bytes pass
  their checksum and shape checks. Do not rebuild or download silently.

## Measures

For each query and arm, retain all returned hits and report:

1. Selected-source recall: fraction of predeclared facts with a matching source
   section in the returned results. Valid sources are not necessarily exhaustive.
2. Reference-page reach: whether the results reach a page containing each fact,
   so the agent could use that page's outline to locate additional sections.
   Reaching a page is not reading the fact.
3. Exact-quote exposure if every hit were read, including `page_context`.
   This is a counterfactual diagnostic, not actual agent reads or semantic recall.
4. Result text size. Eight results can save a later search but supply more text;
   neither token cost nor end-to-end speed is established here.

Recompute the old six-versus-eight comparison from saved rankings, without
changing old grades. For each historical keyword-agent task, measure the union
of its actual recorded search results and its actual read passages separately.
That is descriptive evidence of the existing search loop, not a controlled
estimate of the benefit of query rewriting.

No offline score automatically triggers adoption. In particular, a fixed
ten-point retrieval threshold is not a statistical test or an answer-quality
measure. Failed or incomplete checks remain visible; no wording, references or
fusion weights change after results appear.

## What an eventual live comparison must answer

Use the current writer and auditor, same explicit effort, same sources, same
questions and frozen assertions. Include the observed gain cases, loss case and
exact-API controls; alternate order and use repeated paired attempts. Judge
scores need source-based review of omissions, citations and code, with retrieval
arm labels hidden during review. Measure completed tasks, material defects,
planner calls, cost and latency together. Preserve all attempts.

Fresh wording of known tasks remains development evidence. A selected-target
comparison can diagnose whether retrieval improves those tasks; a broader claim
requires new information needs. Configure and cost that live run separately.
This offline follow-up does not authorize or initiate it.
