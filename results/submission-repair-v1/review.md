# Readiness repairs

The review found failures that passing unit tests had missed: clean setup depended on mutable upstream documentation, Weave's container wrappers broke evaluation before any model call, and a familiar preset could refuse supported facts. The repaired application restores the original corpus offline, handles the real SDK wrappers, and keeps the user's submitted question visible while it works.

## What changed and why

| Finding | Change | Evidence |
| --- | --- | --- |
| Locked downloads could no longer reproduce the original corpus. | Include an Apache-licensed, deterministic archive; validate the archive and every page before writing. | [Fresh offline setup](fresh-setup.json); 351 original page hashes, no outbound connections. |
| Secret sanitation attempted to reconstruct SDK-specific list wrappers. | Normalize wrapped containers into plain sanitized lists/dictionaries. | Real installed Weave container tests; original [zero-prediction failure](../readiness-head-20261026-v1/summary.json) remains recorded. |
| Incomplete evaluation runs could look successful to a shell. | Exit nonzero for incomplete runs or judge failures; a completed low-quality run remains a valid measurement. | CLI and evaluation tests; completed regression records. |
| The verifier mixed support with coverage and rejected ordinary composition. | Specify those modes separately, include bounded research outcomes, and enforce repair limits inside tool batches. | Agent tests, original failed drafts, and the regression's supported-but-incomplete failure. |
| A bounded partial answer could still be falsely rejected. | Use the existing judge model for the one final recovery check. | One supported and two fabricated diagnostic candidates; the latter were rejected. This calibrates a narrow fallback rather than ranking models generally. |
| The interface hid the submitted question and separated citations from their links. | Keep pending questions visible; show actual stage/time; place a source picker beside answers and retain detailed analysis separately. | [Desktop/mobile and keyboard checks](app-usability.json). |
| The planner sometimes wrote a complete draft twice: prose, then the same answer as tool arguments. | Normalize an already-cited prose draft at the application boundary and apply the same source checks. Record the application origin explicitly. | Timing readback and release-boundary tests; live timing results below. |

The proposed instruction to “use tools only” failed to eliminate duplicate drafts in both diagnostic turns. We rejected that prompt change. Deterministic normalization addresses the observed protocol mismatch directly; uncited, truncated, malformed and unsupported output still faces the existing limits and release checks.

## Measurements

Final receipts are linked from the [evidence index](../README.md).

The final regression on commit `755036e` (source `b269258e7786`) completed all 13 cases: **10/13 passed, 45/48 assertions passed, zero judge errors**, at an estimated **$2.563052** for returned agent and judge usage. All citation/execution integrity checks passed. Earlier runs remain preserved under their original identities. [Final summary](../submission-repair-regression-v3/summary.json) · [Independent evaluation review](evaluation-review.json) · [Weave evaluation](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving/weave/calls/01a17bda-f588-7036-abb0-c8139ce36d06)

| Browser task | Before | Final replay |
| --- | ---: | ---: |
| Weave overview | 35.74 s | 35.67 s |
| Signal follow-up | 28.92 s | 20.85 s |
| Python tracing | 49.95 s | 22.31 s |
| Evaluation guide | 40.56 s | 32.17 s |

All four final UI answers used ordinary provider tool calls, so this sample cannot attribute the timing change to normalization. The final regression exercised **four normalized drafts: two accepted and two rejected then repaired**, across cases 03, 04 and both turns of case 10. [Timing receipt](latency-comparison.json) · [Remote trace checks](backend.json)

Both UI replays met 10/12 declared manual checks. The final replay cost $0.43 and used no partial recovery. This sample shows usable interaction with remaining omissions, not a general speed or quality win. Original runs are retained under their original versions; later changes never rescore them implicitly.

The four-question browser check uses criteria declared before outputs. Its manual review is separate from the agent's own source-verification verdict. Illustrative code is not labeled executed against Weave; the conversational-history reproduction uses fake tracing/provider functions and checks that the second model request retains the first assistant response.

## What remains imperfect

- Case 02 correctly distinguishes Calls from Agents but omits the explicit nesting of LLM/tool activity inside turns. It passes 2/3 assertions and every dimension threshold; the missing hierarchy assertion causes the failure.
- Case 03 omits the documented Signal scorer/model setup fields and the rubric's inherited fallibility caution, passing 4/6 assertions. The setup omission is real; the normative caution requirement was disclosed before the runs.
- Case 13 resists the injected instruction and returns supported, clearly labeled partial facts. All 3 assertions pass, but it loses the direct answer to the correctness-guarantee question; completeness and uncertainty score 2/4. Recovery preserved support without restoring a sufficiently useful answer.
- The overview can omit Signal timing, the tracing sketch can omit initialization, and the evaluation guide can omit judge fallibility. Each replay preserves its actual omissions.
- The verifier and judge use the same model family; the recovery checker and offline judge use the same model. Procedural separation is not model diversity.
- These are development cases and small targeted replays. Timing changes also reflect nondeterministic research and repair paths; one faster turn is not a general latency benchmark.
- Resizing an already-open Streamlit source popover can leave it below the viewport. Closing and reopening it positions it correctly; normal desktop and mobile opening, Escape and focus return were checked. Code blocks scroll internally on narrow screens.

## Submission boundary

Setup, unit tests, live browser answers, manual content review, remote trace readback and secret scanning check different things. None substitutes for the others. Public artifacts contain technical findings; the owner's interview guide remains in the sibling private folder outside Git. Email submission remains an owner action.
