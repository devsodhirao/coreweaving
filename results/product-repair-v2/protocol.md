# Final product verification

Frozen before submissions. Runtime uses a separate Opus 5.5 verifier at medium effort, Sonnet 5.5 planner at medium, unchanged release checks and rubric 2.3. It preserves SDK dataset-row references in legacy telemetry. No prompt, corpus, retrieval, limit or rubric change.

Run the original six app tasks/seven turns once each, preserving the Anthropic follow-up conversation, and separately click the actual Understand Weave preset once without the documentation-URL prefix. Keep all failures; no regeneration. Inspect sources and generated code against the same frozen18criteria. The overview timing criterion remains despite exceeding the literal question. Use an additional independent review rather than treating the internal passed flag as quality.

Only after the actual preset delivers a useful answer, run the unchanged13-case regression once, named product-repair-regression-v2, budget7USD. Read back the evaluation parent, indexed rows, Agent roots/model spans and usage. UI observed stop3USD, not an account cap; one240second timeout per turn. No Claude rerun or new model arm.

Check599local tests and Ruff, fresh locked clone, desktop1440/mobile390 layouts, Sources and analysis controls, configured-key exclusion, public links. Keep prior13/13and12/13runs attributed to their versions. This is reused development evidence; neither the four-candidate verifier probe nor this replay establishes general superiority over Claude.
