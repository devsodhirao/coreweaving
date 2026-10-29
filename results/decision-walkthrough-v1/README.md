# Current app walkthrough and wording review

Two real browser turns ran on October 29, 2026, using source
`b312a2c9a081ed88cd7f9a4a8780aa4ba79541cf4cc6a59fb388a74c713991d0`.
The continuation reviewed the saved answers and screenshots, matched their sources,
and read back the stored Weave records without regenerating answers.

This is a focused walkthrough, not a full evaluation or a before/after comparison.
The earlier regression's scores still belong to its own runtime.

| Question | Recorded outcome | Full rendered answer | Model-use estimate |
| --- | --- | ---: | ---: |
| Understand Weave preset: how tracing, evaluations and Signals fit together | Answered directly; three drafts and three model checks. Useful roles/relationship explanation, with a scoring-scope qualification below. | 57.92 s | $0.6036 |
| When do those Signals run, and can they stop a bad answer before the user sees it? | Retained the context and answered the timing/prevention question. One draft/check. | 43.73 s | $0.4101 |

Total estimated model use: **$1.0136**, within the recorded $2 walkthrough allowance.
It excludes Signal inference and unreturned charges. Engine times were 57.11 and
41.34 seconds; the browser timings above include delivery/rendering. Neither is a
new benchmark median. [Protocol](protocol.json) · [Browser receipt](browser-summary.json)

## What the actual answers reveal

The overview makes the main roles understandable and answers a broad question
without asking an unnecessary clarification. It distinguishes agent tracing from
legacy Calls. It describes Signals as scoring conversations or spans, however,
without stating the completed-turn target. The source introduction already says
agent turns. This is an imprecise operational explanation accepted by the checker;
do not treat it as a clean demonstration of precise Signal scope. The original
broad request did not explicitly ask for every timing detail, so no new numeric
benchmark grade is assigned after the fact.

Its first audit caught an unread source behind the legacy-Monitors advice and an
unsupported suggestion that evaluations consume trace records. The second
challenged the before-release framing. The agent read and revised accordingly.
That demonstrates a working repair path; it does not isolate how much the checker
adds to quality overall. Auditing consumed **23.94 engine seconds** and **$0.3772**,
about **63% of this answer's model cost**. Whether those repairs justify the expense
is an open engineering question.

The follow-up explicitly identifies completed turns, explains the asynchronous
scoring event, and separates monitoring from inline checks. Its sources include
the remote-scorer guide and the guardrails guide. Its final recommendation about
things that must never reach users should not be read as a guarantee that any
guardrail catches every bad output. Both answers could be shorter: the overview
has 339 whitespace-separated words against a prompted target of 150–250; the
follow-up has 416. Plain-language instructions do not guarantee concise output.

This review is AI-assisted inspection of the saved answers and source text, not
an independent human evaluation. [Overview](turn-1/result.json) ·
[Follow-up](turn-2/result.json) · [Source and cost checks](source-checks.json)

## What was verified

- All 26 inspected passage occurrences match the saved corpus text and page
  checksums: nine in the first record and seventeen in the second, including
  retained evidence. These are not 26 independent sources. Declared citations
  pass the citation contract. Neither answer contains an executed SDK example.
- Both turns and all **20 provider responses** match stored Weave outputs,
  parentage, identities and returned usage. Local and remote cost estimates agree
  to rounding. [Readback](backend-readback.json)
- The real browser opened Sources & analysis, downloaded each result, and cleared
  the displayed conversation with New conversation. Desktop 1440×1000 and mobile
  390×844 had no recorded browser errors, failed requests or document overflow.
- Ten screenshots were preserved and visually reviewed during the continuation. Some answer
  captures show the scrolled lower part, not the whole answer.
- The wording pass covers the app, terminal output, model instructions, cost
  explanation and README. **430 local tests** passed with 336 existing SDK
  warnings; Ruff and whitespace checks passed. [Local checks](local-checks.json)

No current-model ambiguous-question/reply pair, Python execution, load test or
full new regression is established by these two turns. The screenshot-storage
question is part of the separate retrieval experiment, not this browser replay.
The user's existing session on port 8501 was not reset.

Read the [decision guide](../../docs/DECISIONS.md) for the brief mapping,
screenshots, tradeoffs and open questions.
