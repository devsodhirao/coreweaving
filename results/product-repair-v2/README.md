# Stronger auditor: useful, insufficient on its own

Runtime `3b24cd2`, source `5ed0e00b1591db2b2faf1c4c400dcb8340e3777c89ed0ecfa5310019d99cf459`: Sonnet 5.5 plans, Opus 5.5 verifies, both at medium effort. Release checks, questions and criteria are unchanged.

The same seven actual UI turns passed **16/18 outcomes and 4/6 tasks**, costing **$1.27** with a **33.2-second median visible wait**. All seven completed visibly, but the overview delivered an incomplete answer. The usage follow-up explained the mappings correctly yet supplied code that could access `.text` on a tool/thinking block before recording usage. Passing its explanation criteria did not satisfy the separate usable-code rule. [Independent review](answer-review.json) · [Measurements](summary.json)

A separate click on the unprefixed overview preset produced a useful full answer in **44.9 seconds**, costing **$0.22**. That pass does not erase the prefixed question's failure. Both checks used the actual browser and saved one answer per submission. [Preset receipt](preset-smoke/status.json)

The narrower paired verifier probe had correctly suggested Opus was better on two stored supported drafts, with both models rejecting the two fabricated controls. This full replay shows why a component probe is insufficient: the writer can still add an unsupported extra claim, consume its repairs and lose the answer in fallback. [Verifier probe](../product-verifier-probe-v1/summary.json)

The planned regression for this intermediate configuration was not run. These UI failures justified testing the stronger writer first; [two full-turn probes](../product-writer-probe-v1/review.json) and the [final frozen protocol](../product-final-v1/protocol.md) record that change. No rubric or completed score was changed.

[Backend readback](backend-readback.json) verifies 8/8 turn roots and 55/55 model spans, split into the seven-turn benchmark and separate preset. It faithfully records the incomplete answer; telemetry delivery is not quality approval. [Fresh setup](fresh-setup.json) restores 351 pages offline; [local checks](local-checks.json) record 599 passing tests.

The dataset-reference repair is independently checked by a [deterministic one-row evaluation](../product-index-repair-v2/interpretation.json). Its parent, indexed row, prediction and directly queried scorer all match; the endpoint omits its optional scorer-ID map. An earlier [raw URI-only scalar fixture](../product-index-repair-v1/diagnosis.json) exposed a separate Weave 0.54 EvaluationResults-table limitation. Neither fixture uses a model.
