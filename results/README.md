# Evidence index

All files contain recorded outputs or explicitly labeled fixtures. No example results are presented as real agent executions.

| Evidence | Result and scope |
| --- | --- |
| [submission-v1](submission-v1/summary.json) | Latest full `weave.Evaluation`: 12/13 pass, evaluated commit `1c39ad8`, source/dataset/snapshot hashes recorded. Individual answers and judge explanations are in `cases/`. |
| [Submission delivery recovery](submission-v1/remote-recovery.json) | Actual completed evaluation record replayed through `calls_complete` after the eager end endpoint returned 502. Original timestamps and scores preserved; remote output verified. |
| [baseline-v1](baseline-v1/summary.json) | Earlier 13/13 run before page introductions were attached to every passage. Local results complete; its parent call end was not ingested. Not a controlled comparison with the submission run. |
| [pipeline-check](pipeline-check/summary.json) | Initial three-case check, 3/3. Same parent-call delivery problem; per-case evidence preserved. |
| [delivery-check](delivery-check/summary.json) | One real clarification case, 1/1, after the transport fix at `d98a17c`. The harness automatically recovered delivery and read back the correct summary. This is not a second full evaluation. |
| [Judge calibration](judge-calibration.json) | Supported recorded answer accepted; synthetic false guarantee rejected despite a real citation ID and passing verifier metadata. Two diagnostic fixtures, not held-out performance evidence. |
| [Signal setup](signal-setup.json) | Active new-agent Monitor, model, prompt, sampling, and labeled negative fixture ID. |
| [Signal feedback](signal-feedback.json) | Background `wandb.agent_monitor` feedback from the active monitor, including tag, reason, confidence, and exact trigger/scorer references. |
| [Initial successful Signal feedback](signal-feedback-initial.json) | Earlier proof during the integration diagnosis. Retained separately from the final setup receipt. |
| [Signal filter verification](signal-filter-verification.json) | Included agent failure versus excluded evaluator control, with exact monitor query and observation window. Earlier prompt-only filtering was insufficient. |
| [Fresh install](fresh-install.json) | Separate checkout, locked dependency install, 351 docs restored from upstream, 15 passing tests, and an actual checked answer. |
| [Trace verification](trace-verification.json) | Two actual two-turn conversations, their model/tool/verifier span counts, recorded token usage, and trace IDs queried from Weave. |
| [Interface review](ui-review.json) | Layouts at 390, 768, and 1440 pixels; plan and guide navigation; actual starter submission and evidence panels; final two-turn conversation after the input transition fix. All 16 local tests passed, including a fake-agent regression for repeated submissions. Separate from the 13-case quality evaluation. |
| [Usage and answer-library check](learning-foundation.json) | Two real turns in one conversation, preserved context/evidence, all-call usage and local unreviewed records. Estimated model charges $0.304304 and $0.116720 ($0.421024 combined). First answer required one revision. This is a functional check, not a new quality evaluation; no owner acceptance or comparative efficiency claim. Includes implementation hashes and test scope. |

The failed latest case is [03-tracing-and-signals](submission-v1/cases/03-tracing-and-signals.json). It received 4/4 correctness and 2/4 uncertainty, primarily for omitting the expected caution about fallible monitoring. The judge also questioned text from a page introduction that was actually supplied in `page_context`. The judgment is retained as recorded; manual calibration remains useful.

Internal source-check success, structural checks, judge quality, and online review tags measure different things. None establishes a correctness guarantee. The 13-case dataset was used during development; no general accuracy or adoption claim follows from it.
