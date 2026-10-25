# Coreweaving reviewer handoff

This is the entry point for an independent review. The repository is the source of truth; the chat transcript is not required.

Before implementing the next evaluation pass, read the [review of Claude's proposal](AI_BUILD_LOG.md#review-of-claudes-proposed-evaluation-pass--2026-10-26) and its [audit receipt](../results/proposal-review.json). It accepts the coverage/evaluation direction with corrections to scoring, trial persistence, comparisons and scope. That proposal has not been executed.

**Current pass: implemented and verified; research Site published.** Baseline before this pass: `d3c24e8` on `main`. Read `git status --short` and `git log -3 --oneline` before reviewing; those identify the current checkout and any subsequent work. The research and library checks are recorded in [learning-foundation.json](../results/learning-foundation.json).

## What we are building

The CoreWeave DevRel assessment asks for a Weave documentation agent with a dynamic tool loop, multiple turns, self-verification, the new agent tracing model, online Signals, and at least ten evaluated questions with an LLM judge. The public repository and Weave project are already published. The owner must still practice explaining the code and send the submission email.

The owner then asked us to research specialist routing and knowledge graphs in parallel, leave room for voice and adaptive presentation, and build an answer library together through the actual agent. They want to understand costs, efficiency, and whether an answer covers the whole question. Use Weave where it makes those decisions inspectable without adding infrastructure just for demonstration.

## Read these first

1. [README](../README.md): runnable setup, architecture, results and limitations.
2. [Working plan](../plan.html): original brief and product direction.
3. [Research room](../research.html): sourced recommendations, interactive routing scenarios, cost illustration and experiment gates.
4. [Evidence index](../results/README.md): actual runs and their scope.
5. [AI build log](AI_BUILD_LOG.md): observed mistakes, corrections and tradeoffs.

## Implemented versus proposed

| Area | Current state |
| --- | --- |
| Agent | One direct tool-calling research loop, separate evidence verifier, bounded repair and six-exchange memory. Prompts, tool policy and retrieval are unchanged in this pass. |
| Tracing | Actual new-model conversations, turns, LLM and tool spans. Usage comes from provider responses. No autonomous worker agents yet. |
| Signals | Active `needs-review` monitor using CoreWeave Serverless Inference. Recorded fixture feedback and an agent-name filter check. New cost/conflict Signals are proposals. |
| Evaluation | Latest full evaluation is **12/13** at `1c39ad8`; it is not a new run of later interface/instrumentation changes. Preserve the failed case and judge commentary. |
| Usage foundation | New common wrapper counts planning, verification and repair calls. Dated standard-API estimates, cache categories, partial/unknown usage, research counts and Weave attributes. |
| Answer library | New local SQLite persistence for actual UI turns, context, sources, snapshot, usage, trace and separate human review/history. Excluded from Git; never used as retrieval authority. |
| Routing/specialists | Researched proposal. Keep the tested single-agent default. Try clarification/single-research routes and at most two workers only for independent tasks, under one shared budget. |
| Knowledge graph | Researched proposal. First compare BM25 with bounded traversal of explicit links/reviewed relationships. Original passages remain authority. Full extracted GraphRAG is deferred. |
| Whole-story checking | Current verifier checks cited evidence and page-context warnings. Explicit task obligations, missing prerequisites, uncited counterevidence and conflict coverage remain proposed improvements. |
| Voice/adaptive GUI | Researched proposal. Editable speech transcript enters the same agent. A small validated set of response layouts; no generated executable UI. Neither is enabled. |
| Dataset promotion | Existing evaluation dataset is published. Promoting selected library examples into a new public dataset is a separate deliberate future step. No automatic publishing. |

## Decisions and reasons

- Preserve the current default while testing one change at a time. Multiple agents can lose shared context and increase costs; specialist names are not evidence of specialization or accuracy.
- Distinguish an execution graph (which step runs next) from a knowledge graph (which source/concept is related). Neither by itself validates a claim.
- Keep one coordinator responsible for the complete question, assumptions and final evidence. If workers are added, do not call `Agent.run` unchanged inside them: it creates root turn boundaries and mutates conversation history. Use nested Weave sub-agent spans and verify actual parent IDs.
- Treat a graph edge as a retrieval lead. Store relation provenance and workflow/version context; read the underlying source before citing it.
- Separate source-check success, human acceptance and source freshness. A cited answer can still omit a necessary caveat. The existing failed evaluation is a concrete example.
- Use Weave for traces, comparisons, Signals and versioned test datasets. Keep the app focused on a useful answer, a compact usage/evidence receipt and review controls.
- Measure total work for failures and repairs too. Later compare cost per human-accepted answer, latency, missing task parts, contradictions and repeated work; do not treat page count as quality.

## Review targets

- [agent.py](../src/coreweaving/agent.py): `MeteredModel`, per-turn call slicing, context preservation, verifier path and returned metadata. Instrumentation must not change accepted-answer policy.
- [llm.py](../src/coreweaving/llm.py): returned provider model/response identity and existing explicit Weave spans.
- [metrics.py](../src/coreweaving/metrics.py): all-call accounting, exact model rates, distinct cache categories, failed/malformed usage, unknown prices and estimate scope.
- [library.py](../src/coreweaving/library.py): idempotent records, unchanged original result, review history, file permissions and persistence.
- [app.py](../app.py): no paid call on navigation/review/rerun, locally saved completed turns, clear partial estimates, prior context and stale-snapshot warning.
- [tests](../tests): meaningful failure cases rather than tests that merely reproduce implementation details.

## Evidence and limits

The final local suite passed **44 tests**, including Docker isolation, UI reruns and library review, unknown/malformed usage, cache rates, failed calls, repair accounting and follow-up isolation. The [live browser record](../results/learning-foundation.json) contains two actual turns, with estimated model costs of $0.304304 and $0.116720. Human review states remain unreviewed. Library navigation and phone/desktop views were checked, and records survived a restart without extra model calls. The research page passed phone/tablet/desktop layout, keyboard-tab, scenario and calculator checks. The research tracks used primary sources and inspected local code; no routing/graph/voice quality gain has been measured.

Cost is a dated USD list-price estimate for returned usage, not an invoice. It excludes Signals, separate evaluation judges, voice, hosting, taxes and usage not returned after SDK/provider retries or failures. A “model call” is an application invocation, not every HTTP attempt: the Anthropic SDK retries internally. Source snapshot, context and provider model are retained in library records; an exact prompt/implementation fingerprint is not yet stored per library record. The live-check evidence can separately bind its implementation hash. Do not claim more reproducibility than that.

We also read the actual conversation back from Weave: two completed turns, 13 chat spans, three verification-tool spans, matching provider response IDs and token totals. Weave's own summed chat-cost estimate matches the local $0.421024 within floating-point tolerance. Per-turn cost, call-count and unpriced-call attributes also read back correctly. The receipt includes this reconciliation. Do not double-count parent aggregates or describe either estimate as a bill.

The owner-private hosted Site is a planning artifact. The GitHub repository and Weave project are public. Local SQLite records and `.env` remain outside Git. Never print or commit credentials, change billing, or send the submission email during a review.

## Verification commands

From `/Users/devinder/code/coreweaving`:

```bash
git status --short
git log -3 --oneline
uv run pytest -q
uv run ruff check .
git diff --check
```

The app is at `http://127.0.0.1:8501`; the local plan is at `http://127.0.0.1:8766` and research at `http://127.0.0.1:8766/research.html`. The [hosted research page](https://coreweaving-field-plan.modest-cove-1723.chatgpt.site/research.html) is published under the existing owner-private access policy. Site source commit: `38f77c31079fda6a63030cb61a94b5bdf8d6857a`; successful deployment: `appgdep_6ade8b7296888191913aeff3c10f717e`. The live app calls paid APIs when a question is submitted. Reading existing library entries and the plan does not submit a model request. Tests use fakes except local Docker execution. Do not run the full paid evaluation merely to inspect the code.

Please return findings with severity, exact file/line, reproduction or evidence, and the practical consequence. Distinguish bugs, missing evidence, and optional product ideas. Suggested focal question: does the cost/library foundation make it easier to choose the next experiment without overstating accuracy or Weave coverage?
