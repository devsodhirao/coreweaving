# Synthetic fixture assessment

**Hold the claim that the integration works.** These fixtures establish neither a completed evaluation nor verified backend delivery. They also do not demonstrate an application-quality failure or lost traces.

- **Evaluation:** [run.json](run.json) expects 13 predictions but records zero predictions and zero model calls. Its `complete` status and exit code 0 conflict with that expected workload. Treat this as an incomplete or incorrectly classified evaluation, with quality unmeasured (`quality_score: null`), rather than a passing run or a 0% quality score. The fixture does not identify the cause.
- **Tracing:** [mcp.json](mcp.json) describes Conversation SDK instrumentation but queries the classic Calls surface through a `models-weave` profile. The listed tools provide no Agents-span query. Zero Calls therefore does not resolve whether the recorded conversation trace reached the backend. A local trace ID and successful flush establish neither stored parentage nor message/usage fidelity; backend delivery remains unverified.

The next authorized checks are local and read-only:

1. Inspect the evaluator's row-loading, prediction-dispatch and completion-summary paths, plus existing logs. Reconcile the expected 13 rows with actual processed rows and identify where work stopped. Check whether a receipt validator rejects a `complete` result with missing predictions while preserving the null quality score.
2. Inspect the application's lockfile, initialization and exporter configuration without exposing secrets. Establish the actual SDK version, intended project and tracing surface; the fixtures omit SDK identity and use `runtime_commit: fixture-only`, so no deployed source correspondence is established.
3. Inspect any existing local exporter/trace receipt for the recorded trace ID. Compare actual model/tool attempts, messages, parentage and usage with exported spans, recording absent evidence explicitly. Prepare the exact Agents query and expected counts for a later authorized backend check; do not infer its result from the Calls query or change the deployment profile during this review.

No remote queries, model calls, installation, configuration changes or new evaluation runs were performed. These are synthetic fixtures, not observations of a live integration. End-to-end readiness, quality, latency and cost remain unmeasured here.
