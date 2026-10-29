# Retrieval experiment

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
