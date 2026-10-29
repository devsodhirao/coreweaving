# Observed lessons, not universal product rules

These lessons come from Coreweaving's October 2026 development records. They describe mechanisms to investigate, not expected behavior of every Weave release.

| Observation | Reusable decision |
| --- | --- |
| A source-supported overview omitted a requested relationship; a later bundled outcome still passed on a generic clause. | Check requested parts independently when needed. IDs and literal quotes establish structure and provenance, not semantic fulfillment. Keep focused questions narrow. |
| A richer verdict hit its output limit on a negative and omitted required evidence anchors on a positive. | Test delivery under real limits before interpreting semantic scores. Fail-closed rejection of malformed output is not a successful negative-control judgment. |
| A classifier tagged a cited answer as uncited despite acknowledging its citation. | Use program state for eligibility when possible; reserve model judgment for what cannot be computed reliably. |
| A verifier copied a valid sentence without citation markers; a literal guard rejected it. Later, positive-claim code summaries still blocked useful answers. | First distinguish report validation from semantic truth. If the positive inventory adds failures without demonstrated value, test a smaller exceptions-only report using both valid answers and substantive negatives. [Control review](https://github.com/devsodhirao/coreweaving/blob/main/results/essence-v1/auditor-check-v1/semantic-review.json). |
| Plain-list fixtures passed while real Weave container values crashed evaluation. | Include a realistic SDK-boundary test; zero predictions is an infrastructure failure, not a quality score. |
| Evaluation outputs stored a source hash as an SDK object reference; resolving it matched all 13 rows and their nested turn hashes. | Preserve and dereference stored references before comparing values at the same schema level. Unresolved references are unverified, not mismatches. [Readback receipt](https://github.com/devsodhirao/coreweaving/blob/main/results/task-completion-repair-v1/backend-intermediate-5d-source-resolution.json). |
| An evaluation parent and summary matched while only 2/13 evaluation rows were present; all Agent traces arrived separately. | Verify expected child records independently of the parent and the Agent data plane. Preserve missing exports instead of reconstructing successful-looking records. [Diagnosis](https://github.com/devsodhirao/coreweaving/blob/main/results/task-completion-repair-v1/backend-retry-missing-rows-diagnostic.json). |
| Source-only and no-verifier arms tied on factual assertions while case passes differed. | Inspect what the aggregate rewards; add a citation-only control before attributing benefit to a model auditor. |
| Later repair improved a reused suite after two justified assertion changes. | Disclose development-set reuse and instrument changes; preserve unchanged-assertion comparisons. |

Collected data becomes useful when it changes a decision and a subsequent check tests that decision. Retain representative failures, positive controls, attributable execution receipts and concise conclusions. More traces alone do not establish improvement or train the model.

Project records: https://github.com/devsodhirao/coreweaving/tree/main/results
