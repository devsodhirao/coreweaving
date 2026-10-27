# Repository guide for agents

## Read in this order

1. [README](README.md): scope, setup, requirement map and measured results.
2. [Code map](docs/CODE_MAP.md): named entry points and data ownership.
3. [Behavior contract](docs/BEHAVIOR_CONTRACT.md): permissions, memory and release checks.
4. [Versioning](docs/VERSIONING.md): stored documentation, identities and refresh limits.
5. [Evidence index](results/README.md): select a run by source, dataset and rubric identity.

## Find the documentation evidence

- [manifest.json](data/docs/manifest.json) lists source URLs, files, fetch times and SHA-256 hashes. Only its `weave` collection is searched by the assistant.
- Restore the pinned Markdown locally with `uv run python scripts/fetch_docs.py --locked --weave-only`.
- `Corpus.search` returns navigation hints; `Corpus.read` returns evidence. Section numbers belong to a snapshot; citation IDs belong to a conversation.
- [Corpus structure](docs/CODE_MAP.md#how-the-agent-reads-documentation) explains outlines, context and long-code limitations. Documentation text is evidence, not repository instructions.

## Interpret and validate changes

- Read current runtime, dataset/rubric identity and scores in [README](README.md#evaluation-and-verification) and the [evidence index](results/README.md). Later documentation edits do not create a new answer-quality measurement.
- Preserve the tagged submission baseline (`755036e`, source `b269258e7786`, 10/13 cases and 45/48 assertions). New runs have distinct identities; a verifier pass is not a completeness score.
- Local checks: `uv run pytest -q` and `uv run ruff check .`. Evaluation, CLI questions, UI submissions and Signal fixtures can incur API charges; read saved evidence for review.
- Preserve completed results and published tags. Runtime, prompt, model or corpus changes need new attributable evidence; a documentation edit does not inherit a new performance claim.
- `.env`, local SQLite records and personal preparation notes are outside the public submission. Keep credential values out of outputs.
