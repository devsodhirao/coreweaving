# Optional experiments

The application does not import these runners. The required regression and
capability evaluations remain in `coreweaving.evaluate`; these scripts support
separate, explicitly requested investigations. All completed evidence stays in
`results/` with its original runtime and rubric identity.

| Runner | Command from the repository root | Boundary |
| --- | --- | --- |
| Verifier comparison | `uv run python -m scripts.experiments.compare --name new-comparison --trials 2 --budget-usd 10` | Paid agent and judge calls. New runs compare current `off` and `support` modes; old coverage records remain readable by `compare_records`. |
| Cache transport probe | `uv run python -m scripts.experiments.check_experiment cache --name new-cache-probe` | Paid calls with a $1 estimated budget. Measures identical requests with caching changed. |
| Judge calibration | `uv run python -m scripts.experiments.check_experiment calibration --name new-calibration` | Paid calls with a $1 estimated budget. Four labeled fixtures, not general judge validation. |

Names must be new: these runners refuse to overwrite existing results. Replaying
the retired three-arm coverage experiment requires its recorded Git revision;
running today's code does not reproduce that earlier policy.

The evaluation judge now disables prompt caching independently of the agent. The
[last full run](../../results/product-final-regression-v1/summary.json) wrote
221,142 judge cache tokens and read zero. Each question changes the assertion
schema in the tools, invalidating the reusable prefix. This removes cache-write
overhead without changing the frozen assertions, judge prompt or answer checks;
the agent still caches repeated conversation context.

## Retrieval experiment

These helpers compare search backends while using the assistant's existing
`Agent`, source reads, verifier, judge and budget. The app still uses
`coreweaving.corpus.Corpus`; importing or running this experiment does not change
its default. No vector database or embedding service is required.

| File | Responsibility |
| --- | --- |
| `retrieval_backend.py` | Source-derived context, local embeddings, fixed rank fusion and validated index cache. Inherits the original evidence reads. |
| `retrieval_compare.py` | Frozen-question validation, retrieval metrics, candidate selection and a bounded paired `weave.Evaluation`. |
| `summarize_retrieval.py` | Recompute paired totals from saved records without API calls or grade changes. |
| [`retrieval-probe.json`](../../evals/retrieval-probe.json) | Questions, evidence nuggets, literal references and answer assertions. |

The [protocol](../../results/retrieval-comparison-v1/protocol.md) defines selection
and adoption rules. The [instrument review](../../results/retrieval-comparison-v1/instrument-review.json)
records fairness corrections made before any search results were observed.

**[Recorded result and decision](../../results/retrieval-comparison-v1/README.md): keep BM25 as the app default.** The hybrid candidate missed the predeclared offline improvement threshold. The experiment remains available for inspection and a separately specified future comparison.

The [current-runtime offline follow-up](../../results/retrieval-followup-v2/README.md)
finds hybrid gains on two fresh wordings and explains why the earlier live subset
did not test the main benefit. Its small replay script reuses these helpers and
validated local vectors. It does not change the app or run a paid evaluation.

## Model setup

Use the base repository's locked setup first. FastEmbed is an isolated experiment
dependency; the following command does not edit the app's lockfile. It downloads
a public embedding model, not a generative API model. The adapter loads ONNX and
tokenizer data locally; it does not enable remote Python code.

```bash
uv run --frozen --with fastembed==0.9.1 python - <<'PY'
from huggingface_hub import snapshot_download
from scripts.experiments.retrieval_backend import MODEL_FILES, MODEL_REPOSITORY, MODEL_REVISION
snapshot_download(
    repo_id=MODEL_REPOSITORY,
    revision=MODEL_REVISION,
    allow_patterns=list(MODEL_FILES),
    local_dir=".agent-cache/bge-small-pinned",
)
PY
```

The model is [BGE-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5),
using [Qdrant's quantized ONNX export](https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q)
and [FastEmbed](https://qdrant.github.io/fastembed/Getting%20Started/). Model files,
package versions, source bytes and index contents are recorded in arm identities.
Long passages use overlapping token windows so their tails are not silently lost.

## Commands and boundaries

```bash
uv run --frozen --with fastembed==0.9.1 python -m scripts.experiments.retrieval_compare offline
# Paid agent and judge calls, at most six paired tasks, shared $5 estimated budget:
uv run --frozen --with fastembed==0.9.1 python -m scripts.experiments.retrieval_compare live
# Read-only aggregation of the committed result, no optional dependencies or API calls:
python3 -m scripts.experiments.summarize_retrieval results/retrieval-comparison-v1/live
```

The runner refuses to overwrite existing evidence. This directory is a recorded
experiment, not a general benchmark service: use a separate checkout and a new
results directory for a subsequent run. Never delete the original records to make
a rerun appear to be the first attempt. Keep runtime, instrument and backend
identities fixed between offline selection and the paired run.

Reference recall measures discovery of selected sections, not every possible
valid answer source. Some questions cannot retrieve every selected section in a
single search because of the unchanged two-results-per-page cap. Their ceilings
are reported. An agent can still finish those tasks through additional reads.
Offline retrieval results alone establish neither answer quality nor faster UX.
