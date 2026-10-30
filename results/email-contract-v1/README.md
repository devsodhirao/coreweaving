# Check the app against the submission email

October 30, 2026. The two-question walkthrough works on the local app. The
submission email is **not ready to send with its current GitHub links**: public
`main` is still `330a2a9`, and the linked current-evaluation packet returns 404.
Publishing the reviewed local commits remains a separate unfinished action.

Checked local commit `46d8188`, runtime source `b312a2c9a081`. The app, agent,
dependency lock, evaluation inputs and documentation manifest are unchanged from
the measured `a07e5da` build. The existing **12/13 cases and 47/48 assertions**
remain that run's result; this walkthrough adds no new evaluation score.
[Identity](identity.json) · [Publication check](publication-check.json)

## What was exercised

| Email claim | Check and observed result |
| --- | --- |
| Setup works from the README | A clean checkout with an empty dependency cache installed locked dependencies and restored all 351 documentation pages. No credentials were copied or model requests made. [Setup receipt](fresh-setup.json) |
| The preset researches and answers the broad question | Clicked **Understand Weave** on the actual server at `127.0.0.1:8501`. It searched, read sources, revised after a rejected draft and delivered an answer without requesting clarification. [Answer and actions](turn-1/result.json) |
| The follow-up works in the same conversation | Asked exactly: “When do those Signals run, and can they stop a bad answer before the user sees it?” It retained source records, answered the prevention question and distinguished monitoring from inline guardrails. [Follow-up](turn-2/result.json) |
| Sources and checks are inspectable | Opened the evidence dialog, source passages and check/cost panels. All 22 stored passage occurrences match the snapshot, including reused passages; citation and syntax checks found no issues. [Source checks](source-checks.json) |
| The trace describes the actual work | Both turn roots and all **18 provider responses** match remote outputs, parentage, identities and usage. Returned-usage estimates reconcile. [Backend readback](backend-readback.json) |
| Signals review eligible completed turns | Read back the active policy. It still targets `weave.genai.turn_ended`, uses the current filter and references the previously verified scorer. No new Signal fixture or classification was run. [Policy check](signal-policy.json) |
| Downloads and reset work | Both live answers downloaded. Four additional downloads through the actual UI with saved answers matched the originals exactly. New conversation cleared the displayed chat. A reset-only console error remains, described below. [Download check](download-before.json) |
| Desktop and mobile are usable | Checked 1440×1000 and 390×844. No document-level horizontal overflow; evidence controls remain accessible. Screenshots and browser findings are preserved. [Browser receipt](browser-summary.json) |
| Deterministic behavior remains covered | Fresh `uv run pytest -q`: **430 passed**, including real Docker tests; 336 existing SDK warnings. Ruff and whitespace checks passed. [Local checks](local-checks.json) |

## Timing, cost and answer limits

| Turn | Agent execution | Full rendered answer | Estimated model cost |
| --- | ---: | ---: | ---: |
| Overview preset | 43.52 s | 46.52 s | $0.3471 |
| Signals follow-up | 57.51 s | 60.53 s | $0.6260 |

Total **$0.973135** for the two answers and their checks. No paid offline judge
or automatic question retry was used. This counts against the owner's $30 new-work
allowance and excludes Signal inference and unreturned charges. The historical
full-regression cost and median remain separate measurements.

The overview still loosely describes Signals as scoring conversations in places,
rather than consistently naming the completed turn as the scoring unit. The
follow-up explains completed-turn timing directly for remote scorers and labels
the same timing for default LLM scorers as an inference from the documents read.
Our own monitor's completed-turn configuration is separately verified above.
Both answers remain long: 346 and 380 words. These are useful answers with
documented precision and concision limits, not a claim that the checker guarantees
correctness. This interpretation is Codex-assisted review, not an owner label.

[Open the actual two-turn conversation in Weave](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/cd649a13-5b7d-4645-a0f5-9c70fdb549c1)

## Remaining browser issue

After closing Sources & analysis, **New conversation** can generate a console 404
for the previous JSON download URL. The four checked downloads returned the exact
saved answers, and reset succeeded; the error occurred during reset, after the
dialog was closed. No visible application error or failed requested download was
observed. This browser run is therefore not console-error-free.

A fixture-only probe of `on_click="ignore"` reproduced the same reset error,
with all four downloads still correct. That proposed adjustment was not applied
to the app. We preserved the measured runtime rather than adding an unproven
workaround. [Probe receipt](download-ignore-probe.json)

## Screenshots

- [Start](screenshots/01-start.png)
- [Research progress](screenshots/02-research-turn-1.png)
- [Overview, scrolled to its ending](screenshots/03-answer-turn-1.png)
- [Checks and cost](screenshots/04-analysis.png)
- [Exact source passages](screenshots/05-source-passages.png)
- [Mobile answer](screenshots/06-mobile-answer.png)
- [Mobile evidence dialog](screenshots/07-mobile-analysis.png)
- [About and version limitation](screenshots/08-about.png)

The browser used a new isolated session; it did not reset the owner's session.
Temporary saved-answer fixture servers were used only for unpaid download checks
and stopped afterward. The existing server on port 8501 remains the demo.
