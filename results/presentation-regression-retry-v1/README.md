# Full regression on the presentation build

**Current runtime: `a07e5da`, source `b312a2c9a081`.** The unchanged 13-case
regression completed with **12/13 judge-recorded case passes and 47/48 assertions**.
All 13 cases have valid grades. This is one complete run after a separately
preserved [operationally failed attempt](../presentation-regression-v1/README.md),
not a completion view combining selected quality results.

| Measure | Observed result |
| --- | --- |
| Cases / assertions | 12/13 cases; 47/48 assertions; zero ungraded assertions |
| Engine time | Median 31.46 seconds across all 15 turns; range 10.24–70.99 seconds |
| Requests | 97 returned agent model responses, including 23 audits; 13 evaluation judge responses |
| Returned-usage estimate | $5.2549468 for this complete run; no unpriced calls in this run |
| Source checks | 64 stored section occurrences match saved page hashes and expected text, counting reuse; no citation-format or Python-syntax issues |
| Local mechanics | 430 tests passed on these same runtime bytes; the [existing receipt](../decision-walkthrough-v1/local-checks.json) is reused rather than relabeled as a new test run |

The earlier timeout attempt adds **$0.24075 in known usage plus one unpriced judge
request**. Combined known use is **$5.4956968**, with that unknown charge still
unresolved. Estimates exclude Signals, hosting, taxes and unreturned charges.
Engine time excludes offline judging, browser rendering and run setup.

Readback matches all 15 turn roots, 97 agent responses and 13 indexed evaluation
rows with their judge receipts. The [demo readiness check](demo-readiness.json)
confirms the same runtime files on port 8501, stopped previews and clean
desktop/mobile welcome and About screens.

## What failed, and why it matters

For **“How do I monitor it?”**, the assistant asked what “it” meant, but added
uncited descriptions of agent scoring, production-call scoring and deployment
monitoring. It searched for `monitor`, read no page, and cited no evidence. The
answer checker accepted it. The evaluation judge rejected assertion
`reg-06-a3`, which requires any optional product alternatives to be sourced.
The [answer review](answer-review.json) agrees with that failure.

The waiting status and conversation mechanics work independently of this content
failure. A short clarification can need no citations; adding product advice
changes that requirement. The answer also requested the programming language, so
the preferred single focused question is not consistently achieved. No prompt
was changed after measurement to make this failure disappear.

Initialization now includes authentication and routing. The Calls/Agents answer
explicitly places LLM/tool activity inside turns. These are observations from this
trial, not proof that the wording changes caused improvements. The earlier
omissions and reviewer disagreement remain in their original records.

## How to interpret the result

The runtime, dataset, 48 assertions, rubric 2.3, seed, models, effort and cache
settings were fixed before the retry. The writer, auditor and evaluation judge
use Opus. These are reused development questions with one trial each. The separate
source review was AI-assisted and unblinded, not independent human calibration.
No broad accuracy or model-ranking claim follows from this result.

Generated SDK examples were inspected, not integration-tested. One import spot
check confirms that `Message`, `Usage` and `start_conversation` exist in the
installed `weave.conversation` module; it does not validate whole examples.
The actual Python tool case executed only standard-library logic.

The auditor's incremental value remains unproven. It missed the clarification's
unsourced claims here and the targeted defects in earlier controls. The older
browser overview still misses its timing criterion. The current two-turn
walkthrough's long waits and loose Signals wording also remain disclosed.

[Protocol](protocol.md) · [Preflight](preflight.json) · [Manifest](manifest.json) ·
[Summary](summary.json) · [Answer review](answer-review.json) ·
[Source checks](source-checks.json) ·
[Weave readback](evaluation-backend-readback.json) ·
[Evaluation](https://forge.coreweave.com/wandb/devfromlll-learning-layer-labs/coreweaving/weave/calls/01a189ec-8f31-751a-9d8c-8749fb7623ae)
