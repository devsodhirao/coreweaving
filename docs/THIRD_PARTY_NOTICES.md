# Documentation sources

The application searches a local snapshot of the official Weave documentation. Every downloaded page is identified by its original URL, canonical URL, retrieval time and content hash in `data/docs/manifest.json`. Links in answers point back to the original documentation.

Raw documentation is not committed to this repository. Evaluation records include the source passages needed to inspect their answers. W&B's documentation source repository is [wandb/docs](https://github.com/wandb/docs); its Apache-2.0 license is reproduced in `WEAVE_DOCS_LICENSE.txt` alongside this notice. This application's generated code is separate from those upstream documents.

The download utility also saves Anthropic, Streamlit and Forge setup guides locally for development. Those supporting pages are excluded from the agent's search index and from Git. Their respective publishers retain their rights.
