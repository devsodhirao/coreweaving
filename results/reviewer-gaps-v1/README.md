# Reviewer gaps: progress and budget

This work follows the October 30 review request. The total new model-use cap is **$30**. Existing experiments retain their original costs and scores; they are not charged again in this work's ledger.

## Step 0 — existing measurement matches current runtime

The requested newer-build regression had already completed on October 29: [13 cases, 12 passes, 47/48 assertions](../presentation-regression-retry-v1/README.md). The measured commit is `a07e5da`, source `b312a2c9a081`. The checkout at the start of this review was `e1b005d`, a documentation/results commit with identical runtime, locked dependencies and evaluation inputs. The [identity receipt](step-0-identity.json) records the comparison, model settings and saved-result hashes.

Reused that measurement rather than repeat it. **No new regression was run at the later documentation HEAD.** The README still attributes the result to `a07e5da`; this check adds no new quality evidence. Corrected two stale documentation headers that still called `522c320` current. The original tag and completed result files remain unchanged.

[Step 0 checks](step-0-checks.json): 430 local tests passed; Ruff and `git diff --check` passed. These checks made no model requests.

## Completed, proposed and waiting

| Step | State | New model-use estimate |
| --- | --- | ---: |
| 0: match the demo to its measurement | Complete through identity verification and reuse of the existing full run | $0 |
| 1: prepare human labeling | Next; use saved answers and leave all human labels blank | $0 planned |
| 1: agreement and different-family judge | Waiting for owner labels; no agreement measured | Not spent |
| 2–9: repeated trials, feedback loop, analysis and packaging | Proposed; not started in this review | Not spent |

The requested $15–20 repeated-trial run and $5–8 cheaper-writer comparison leave only $2–10 of the $30 cap for the second judge and feedback example. Before any later paid step, freeze its scope and maximum, including judge calls, against the remaining total. Unknown charges are not counted as zero. No paid step starts during the owner-labeling handoff.

The next handoff deliberately stops for the owner. AI-assisted reviews already in the repository are useful diagnostics, **not human labels**. The writer and original judge share the Opus model family. Single-run scores, unproven auditor benefit and the known clarification defect remain disclosed.
