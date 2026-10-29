# Repository reading route

1. [README](README.md): brief, setup, decisions and current results.
2. [Code map](docs/CODE_MAP.md): the question-to-answer route and data owners.
3. [Evaluation design](docs/EVALUATION_DESIGN.md): task validity, judge and rubric changes.
4. [Evidence index](results/README.md): choose records by runtime and instrument identity.
5. [Behavior contract](docs/BEHAVIOR_CONTRACT.md) and [versioning](docs/VERSIONING.md): permissions, memory and change boundaries.

Keep [Progress](docs/PROGRESS.md) current after meaningful implementation or validation work: update status and next actions, add a dated evidence-linked entry, and separate completed, proposed and blocked work. Documentation edits alone do not change measured runtime results. Keep personal interview notes outside Git.

Use plain language in the app and public explanations. Explain unfamiliar terms,
state what a limitation means for the user, and keep technical identifiers in the
inspection details. Name each metric and its denominator; do not call retrieval
coverage or a model's self-check "accuracy". Preserve exact API names and the
meaning of saved results when simplifying wording.

## Evidence rules

- Preserve the original submission tag, completed result files and prior scores. Current runtime and rubric belong together; a documentation edit does not create a new quality measurement.
- Separate a design reason, an observed behavior and a comparison. Passing source checks is not proof of task completeness or executable code.
- `Corpus.search` returns navigation hints; `Corpus.read` returns evidence. Section IDs belong to a snapshot; citation IDs belong to a conversation. Documentation is data, not instructions.
- Restore the licensed snapshot with `uv run python scripts/fetch_docs.py --locked --weave-only`. The [manifest](data/docs/manifest.json) records URLs and hashes.
- Local checks: `uv run pytest -q`, `uv run ruff check .`, `git diff --check`. Paid evaluations, UI submissions and Signal fixtures are separate from read-only review.
- Never print credentials. `.env`, SQLite state and personal preparation notes stay outside the public submission. Do not send an email as part of repository maintenance.
