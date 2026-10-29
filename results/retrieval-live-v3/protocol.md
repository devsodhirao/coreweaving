# Does hybrid help the current agent answer?

Frozen before new model calls on October 29, 2026. The owner requested experiments
before making claims, prefers hybrid, and asked to finish the existing review
without expanding the app unnecessarily.

Use all six unchanged questions, assertions and reference passages from
`results/retrieval-followup-v2/cases.json`: two observed retrieval-gain wordings,
two related workflow/versioning cases and two exact-API controls. These cover five
known information needs; they are development diagnostics, not held-out tasks.

Run **two paired attempts per question: 24 agent turns and 24 judge calls**.
This is smaller than the earlier proposed three-repeat study to bound cost and
work. It can expose repeated concrete differences, not establish reliability or
statistical significance. Alternate arm order within cases and reverse it in the
second repeat. Each attempt starts a fresh session. Preserve every result.

Compare current BM25 with the existing hybrid (contextual BM25 plus pinned local
BGE-small rankings, equal reciprocal-rank fusion, k=60). Keep the six-result
default, two-per-page cap, exact source reads, current prompts, Opus model names,
medium writer/checker effort and support verification unchanged. Reuse the saved
vectors only after their existing exact-identity checks. Hybrid is a package of
context and semantic retrieval, not an isolated dense-only intervention.

Freeze current source, prompts, settings, cases, script, corpus, encoder and vector
identities in `freeze.json`. Baseline is the actual `Corpus`; hybrid uses the prior
experimental implementation. Compare their frozen raw-query rankings with the
earlier offline receipts before paid work. A source change or mismatch stops work.
No parameter tuning or question changes during the run.

Use the current `QualityJudge` with the unchanged assertions and source references.
References are supplied only to the judge. Its generated payload does not include
the arm. Also prepare shuffled answer/source packets without arm, timing, cost or
judge labels for an AI-assisted source review. Record missing prerequisites,
wrong attribution, code defects and unnecessary refusals. Preserve disagreements
with the judge. This is not independent human calibration.

Report by question and repeat: task outcomes, errors, research and checker calls,
queries and actual reads, returned-usage cost, and engine time. Report setup and
search overhead separately; this is not browser latency. Caches remain enabled
as in the app, and returned cache usage is retained. Alternating order reduces
but does not remove provider/cache variation.

**Decision rule:** a repeated answer improvement on an observed gain task, without
a material regression on the controls, supports advancing hybrid. For tied
quality, prefer fewer research requests and a consistent practical time/cost gain;
a one-off faster answer is insufficient. Mixed or tied results leave superiority
unestablished. A user preference can justify a tradeoff, but cannot change the
observed outcome. Any recommendation must include model/index provisioning and
maintenance costs. This targeted run alone does not establish production readiness.

**Spend and stopping:** shared $20 returned-usage estimate allowance for this
experiment, with the existing conservative per-request reservations and SDK
retries disabled. Stop on an operational failure, judge delivery failure, unknown
usage or budget exhaustion; keep incomplete attempts. Do not retry a quality
failure or add repetitions after seeing results. No Signal fixture or new monitor
activation. Existing Signals may consume separate inference credits. The allowance
is not a provider billing cap. Backend readback checks delivery separately.

This is a paired agent experiment using the app and its existing judge. It does
not replace or relabel the brief's earlier `weave.Evaluation` runs. No production
retrieval or dependencies change as a side effect of running it.
