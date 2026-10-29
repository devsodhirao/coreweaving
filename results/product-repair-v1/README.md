# Repair the user-visible failures

**The app now delivers all seven selected turns, preserves the documented Python example and exports every expected turn/model record.** This is a repair of failures exposed by the [actual Claude chat comparison](../claude-product-baseline-v1/README.md), not a new retrieval architecture.

The completed regression is **12/13 cases, 46/48 assertions**. A separate preset-button check still returns a partial answer, and the evaluation row index remains empty despite verified stored predictions and scores. These failures remain part of v1.

Runtime: `81c49c004bfa5ad75e1ad3cbb16b2aa0343d4b78`; source `55c77715c7224fd844a499e93b1a816abfa686db2b848b19991c0a56b28fe794`. The replay protocol was committed as `52a252f` before submissions. The snapshot, six questions, 18 criteria and regression rubric remain unchanged. [Protocol](protocol.md) · [Exact inputs](tasks.json)

## What changed and why

| Observed problem | Repair | Boundary |
| --- | --- | --- |
| Credential masking turned annotations and variable expressions into broken code. JSON re-encoding repeated the damage before model requests. | Parse valid Python fences, mask credential literals, preserve code structure; decode JSON before recursively masking and serialize replacements safely. | Unknown or constructed secrets can escape masking. Other languages and malformed code still use conservative text handling. |
| Source verification accepted syntactically invalid Python. | Parse final Python fences before the model audit; return a repair issue without executing the code. | Syntax is not SDK compatibility or successful execution. Verification-off is experimental and remains unavailable in the web app. |
| Weave interpreted literal `weave:///` text as reference metadata and lost records. | Encode only telemetry copies with a reversible visible marker; preserve real typed SDK references. | Provider inputs, tool queries, evidence and displayed answers are unchanged. Dataset-row reference containers still lose identity; see the regression readback below. |
| A broad overview became nine mandatory workflow checks. | Ordinary outcomes describe requested roles/relationships. Input/trigger/output matrices require an explicit request for those facets. Pin agent planning and verification to medium effort. | Task interpretation remains a model judgment. Offline judge settings are unchanged. This bundle does not isolate effort's effect. |

Files: [config.py](../../src/coreweaving/config.py), [agent.py](../../src/coreweaving/agent.py), [llm.py](../../src/coreweaving/llm.py), [telemetry.py](../../src/coreweaving/telemetry.py). Verification contract is now **4**; citation contract stays **3**.

## Actual UI replay

| Task | Outcomes | Visible wait | Result |
| --- | ---: | ---: | --- |
| Tracing / evaluations / Signals overview | 2/3 | 46.1 s | Useful explanation; omits completed-turn timing and retains unnecessary caveats. |
| Hide private input/output fields | 3/3 | 15.4 s | Documented Python remains valid; baseline code was damaged. |
| Dataset + LLM judge | 3/3 | 26.5 s | Supported evaluation procedure. |
| Direct Anthropic tracing + usage follow-up | 3/3 | 36.2 / 18.3 s | Retains context and explains cache-inclusive usage. |
| Invented hallucination-free API | 3/3 | 20.2 s | Rejects unsupported API/guarantee, cites alternatives. |
| Exact prompt reference/version API | 3/3 | 17.2 s | Supported version/init explanation; complete trace delivery. |

**17/18 outcomes; 5/6 fully passing tasks.** The frozen overview timing criterion exceeds the literal broad question. It remains a failed criterion; the runtime's narrower completion label and the external checklist answer different questions. Neither changes the historical grades. Review is Codex-assisted, not human-calibrated. Fourteen cited passage references match the snapshot; five supplied Python fences parse. Generated SDK integrations were not executed. [Detailed review](answer-review.json)

| Same seven app turns | Baseline | Repaired |
| --- | ---: | ---: |
| Median visible completion | 30.2 s | 20.2 s |
| Returned-usage model estimate | $1.22 | $0.64 |
| Model requests | 47 | 43 |
| Delivered root traces | 6/7 | 7/7 |
| Returned model spans | 43/47 | 43/43 |

The baseline overview's observer missed its completion button: full text was visible at 105.4 s, completion confirmed by 162.7 s. The seven-turn median is unchanged by using either value. Preserve this correction when comparing that turn. [Per-turn receipts](summary.json)

Regular Claude was **not rerun**. The original clean comparison tied on 14/15 outcomes; it used Opus 5.5 / Extra / web tools, while this app uses Sonnet 5.5 / medium / a stored corpus. The privacy pair inherited Claude history and remains excluded from the clean comparison. These small reused tasks cannot establish general product superiority.

## Weave and setup checks

- [Actual app readback](backend-readback.json): all seven root traces, all 43 model records, parentage, answers and usage reconcile. Local $0.6380576 versus remote $0.63805758 differs only by rounding.
- [Literal serialization fixture](telemetry-fixture/backend-readback.json): 22 checks pass across five synthetic Agent spans and one legacy call, preserving typed references. No model requests or invented usage. Its earlier source hash is recorded; the actual app readback validates the final runtime separately.
- [Signal readback](signal-readback.json): existing monitor enabled, completed-turn event and runtime-reason filter match. This checks configuration; earlier [eligible/excluded controls](../task-completion-repair-v1/signal-live-readback.json) supply scoring evidence.
- [Local checks](local-checks.json): 593 tests, Ruff and diff checks pass. [Corpus masking sweep](redaction-corpus-sweep.json): 556 initially valid Python examples survive six paths, including 934 fake provider requests; no network attempts.
- [Fresh checkout](fresh-setup.json): locked install, all 351 pages restored with socket connections blocked, and matching runtime/corpus imports. No `.env` or API calls; dependency package cache was allowed. The first verification harness exited after the restore script's successful `SystemExit`; the corrected harness additionally checked corpus loading and zero connection attempts.

## Completed regression and remote records

The unchanged 13-case suite completed under rubric **2.3**, with **12/13 cases and 46/48 assertions passing**, no failed judges or ungraded assertions, and a returned-usage estimate of **$2.3456047** including the offline judge. Its recorded checkout is `52a252f`, with the same runtime source `55c77715…` as `81c49c0`. [Run summary](../product-repair-regression-v1/summary.json) · [Independent review](regression-review.json)

Case `02-calls-vs-agents` lost the direct answer about `@weave.op` and the conversation/turn/model/tool hierarchy. A premature unread citation, incomplete research of the Ops side of the contrast, and strict negative-inference auditing consumed the three permitted submissions. The final valid research request arrived after the revision cap, and terminal recovery released supported facts with the requested outcome still missing. The two failed assertions are justified. No Python syntax rejection occurred; this is not evidence that the syntax gate caused the failure. The prior runtime's 12/13, 47/48 result failed a different case, so these reused single trials do not establish a quality improvement.

[Backend readback](evaluation-backend-readback.json) verifies **15/15 Agent roots and 84/84 model spans**, plus the completed evaluation parent and matching summary. However, `eval_results_query` returned **0/13 indexed rows**. [Direct exact-ID readback v2](evaluation-direct-call-readback-v2.json) separately verifies all **13 stored predictions and quality scores**, including exact answers and identities; it does not create or prove indexed rows.

[Offline diagnosis](evaluation-reference-diagnosis.json) reproduces the telemetry helper converting a reference-bearing SDK dataset row into an inline dictionary; the remote input has the same shape. Loss of row identity is confirmed. Its causal link to the missing evaluation index is a supported explanation, not an inspected server-internals result. The earlier readbacks remain intact.

## Additional preset-button check

One actual click on “How do tracing, evaluations, and Signals fit together?” completed in **66.568 seconds** and saved exactly one answer. Desktop (1,440 px) and mobile (390 px) showed no horizontal overflow or reported errors; Sources & analysis opened. These are interaction checks, not evidence that the preset answer is fixed. [Browser receipt](preset-smoke/status.json) · [Exact result](preset-smoke/result.json)

The answer is explicitly **partial**, with the relationship outcome still missing despite passing source support. Three rejected drafts were reduced to four supported facts by terminal recovery. This additional turn cost an estimated **$0.2808779** across 11 model calls; it is separate from both the frozen seven-turn replay and the regression totals. [Combined receipt](regression-and-preset-summary.json)

## What this still leaves open

The next repair needs to preserve SDK dataset-row identity and prove indexed row delivery separately from raw call delivery. It also needs to investigate false abstention: incomplete premise research and overstrict treatment of supported synthesis can discard a useful direct answer. The observed failures justify that investigation; they do not establish that changing a prompt or relaxing checks will fix it. Preserve supported and unsupported controls when measuring any correction.

The source verifier can also miss semantic defects; its incremental benefit over deterministic checks has not been isolated. The UI overview remains verbose. Syntax checking does not test the SDK, nullable usage fields or generated integration code. The corpus remains the October 24 snapshot, reference SDK 0.53.1 versus runtime 0.54.0. Current memory is conversation-local, not a persistent user profile.

No rubric changes, model selection contest, hybrid rollout, voice feature, email or submission-tag rewrite was part of this pass. Further work should start from new held-out tasks and independently reviewed failures.
