# AI assistance and engineering decisions

This records work actually performed during the take-home. Codex wrote the application, tests, evaluation harness and documentation. Claude's desktop session helped the owner create/verify accounts, credentials and project visibility; it did not implement the agent. The owner chose the project, requested a plain-language walkthrough, and specified the `devsodhirao` GitHub account and standard Git commands.

The code still needs the owner's walkthrough before the interview: AI assistance does not substitute for being able to explain it.

| Finding | Correction and evidence |
| --- | --- |
| An initial W&B GraphQL project query requested a nonexistent `visibility` field. | Switched to the schema's `access` field and independently checked the public project. Kept keys out of outputs. |
| A presumed OpenAPI JSON URL returned an HTML page with HTTP 200. | Removed it from the download manifest. Added validation so HTML cannot masquerade as a Markdown document. |
| Sonnet 5.5 rejected forced `tool_choice=tool` with HTTP 400. | Checked the current provider documentation. Use ordinary tool selection plus an explicit requested verdict tool, validate the returned structure, and withhold the draft if the verdict is missing or invalid. The failed turn is retained in Weave. |
| Anthropic SDK 2.x emitted its own OTel span in addition to our explicit Weave span. | Disable the provider's native tracing for this client. One provider request has one manually recorded LLM span with messages, purpose and usage. |
| Splitting Markdown on every `#` heading also split Python comments inside fenced examples. | Track code fences when splitting. Added a regression test preserving the complete example. |
| A redirected support URL collided with the landing page's document ID. | Derive identity from the indexed URL and retain the canonical URL separately for citations. Confirmed 351 distinct pages. |
| Tool descriptions alone do not enforce runtime argument limits. | Validate allowed argument keys before dispatch; the model cannot override a snippet's timeout or output cap. Container boundaries are set by code. |
| Weave returned repeated 502 responses when finishing evaluation parent Calls through the eager end endpoint. | Local per-case outputs and summaries survived. An initial `call_end` replay queued the same failing route. The successful workaround uses `calls_complete`, preserving the original call ID, stored input references, true end timestamp, and actual summary. Read the stored call back and compare the summary. The submission and a fresh focused run now have verified remote completion. Earlier runs without a recorded end timestamp are not retrospectively assigned invented times. |
| Publishing a Signal did not produce live scoring. | The initial implementation used `ClassifierMonitor`. Inspecting the installed SDK and official new-Signals frontend showed that this legacy class is excluded by the new workflow. Use `Monitor`, target `weave.genai.turn_ended`, explicitly include turn-context placeholders, and request the `scores` array contract. A direct model probe was useful but insufficient; actual background feedback on a labeled failure fixture proved the new Signal runs. The unused legacy monitor was deactivated. |
| Reading a later section could lose introductory warnings that a page describes the legacy workflow. | Carry the page introduction in `page_context` alongside each passage and tell both planner and verifier to respect it. Add a retrieval regression test. The later run still has one quality failure; do not claim a measured improvement without an ablation. |
| A passing source check did not imply a passing independent evaluation. | All 13 source checks passed, while the latest judge passed 12/13. The failed answer omitted the expected caveat about fallible Signals. Retain the result, inspect the rubric, and discuss the judge's own imperfect citation criticism rather than optimizing the headline. |

A subsequent live Signal tagged an evaluator turn despite the prompt-only exclusion. The correction applies an exact `agent_name == coreweaving` query before sampling. A documentation-agent failure fixture and an excluded evaluator control test that selection independently of the LLM's judgment. This is an observed failure and a code/configuration correction, not a claim that a stronger prompt solves filtering.

## Decisions we can explain

- **Direct loop:** the model chooses tools; Python controls execution, evidence, limits and release of the answer. The whole loop is in one module.
- **Local BM25 search:** no vector database or embedding service during a three-hour exercise. This is cheap and inspectable but weaker on conceptual paraphrases. Repeated queries are allowed.
- **Section evidence:** citations identify the actual passage returned by `read_page`, not just a URL that might support the answer. Search snippets are not automatically citeable.
- **Separate verification:** the verifier sees the proposed answer and its evidence. It has no tools or ability to change the source record. Rejected drafts are not stored as conversation answers.
- **Honest limits:** unavailable Docker, provider errors and research exhaustion are visible. A code sample only counts as executed if the recorded container run succeeded.
- **Independent evaluation references:** expected behaviors and source sections are dataset fields available to the judge, not hints sent to the evaluated model.
- **Live monitoring:** a narrow review-needed Signal has a measurable purpose. It does not pretend to replace claim-level checking or human judgment.

## What the owner should practice

Walk `Agent.run` from a question through one search, one read and a rejected draft. Explain why `@weave.op` alone is not our agent tracing integration. Locate the four judge criteria and change one case's expected behavior thoughtfully. Explain why code execution is offline, what the model can and cannot decide, and why a source-check pass can still be wrong.

The evaluation results and live-trace evidence should be discussed as observations from this run, not broad claims about reliability. Any unresolved integration issue belongs in the submission, along with the attempted workaround.

## Product direction and communication

The owner asked for expectations and an adoption plan in a webpage before further product decisions. The interactive plan separates the original requirements, recorded evidence, and proposed experience. The owner clarified that the brief does not specify a narrow target user. Adding Weave to an existing agent is one demo scenario; the assistant remains useful across the documentation. A first useful action, understandable explanations, and inspectable evidence are the intended advantages. These are product hypotheses, not measured adoption results or claims about LLL's formal methodology. A three-person usability pilot is proposed after the take-home.

The plan and technical guide were checked in a browser for navigation, keyboard tab controls, reading-progress persistence, and mobile overflow. The hosted plan is private; the repository contains a local copy that can be opened without model calls.

## Interface review

The owner asked to see the running product and review its appearance. A real Chrome session showed clipped starter-button text, inconsistent heading styling, and a mobile welcome screen that scrolled partly past its heading. Short action labels with visible example questions, an explicit Streamlit theme, and an inline welcome input corrected those problems. Model and snapshot details moved into an expandable sidebar section; the public-trace notice remains visible above the first input, including on mobile.

The AI-assisted input refactor introduced a functional bug: the history-rendering loop reused `question`, overwriting the newly submitted input. Combined with a rerun after completion, this replayed the previous question. The live browser check caught the repeated requests; the server was stopped and the history variables were renamed. The final real two-turn check completed each distinct question once, retained one conversation ID, and showed one active input. A Streamlit AppTest with a fake agent now checks initial submission, ordinary reruns, a follow-up, conversation reset, and a starter-button submission without spending API credits.

All 16 tests and lint/format checks passed. The [review record](../results/ui-review.json) separates the real browser checks from the fake-agent regression and the earlier 13-case quality evaluation. This pass changes interface presentation and input flow; it does not change the agent's prompts, retrieval, verifier, or execution sandbox.

## Research, usage and the answer library

The owner requested parallel research on routing/specialists, knowledge graphs, voice and adaptive interfaces, with visible cost and whole-story checks. Three bounded research agents inspected the current code and primary sources. Their findings support selective experiments: domain handoffs can lose shared context; documentation links are a lower-cost starting point than full GraphRAG extraction; audio capture still needs transcription and correction. These are design recommendations, not results from our own comparative trials. The owner also asked to use Weave meaningfully without duplicating its dashboards.

The code review exposed a real accounting gap: `planner_usage` counted planning only, even though Weave already recorded verifier usage. A common model wrapper now counts returned usage from planning, verification and repairs; dated rates produce an estimate, while missing/unsupported usage remains unknown. Independent tests caught malformed-token and cache-lifetime handling errors during this change, which were corrected before the passing suite. We do not label the estimate as an invoice or include unobserved Signal/judge charges.

The local answer library stores actual new UI responses, original context and evidence, usage and trace links. Human review is separate from source verification; nothing is approved automatically. Review history and snapshot differences are retained. The library is excluded from Git and never used as factual retrieval input. The current prompts and retrieval strategy remain the same. Whole-task verification, graph expansion, specialist routing, voice and adaptive response layouts are still proposals in [the research room](../research.html).

| Finding during the live walkthrough | Evidence | Consequence and next action |
| --- | --- | --- |
| Verification is a material part of this answer's cost. | The first real question used eight model calls: six planning/drafting and two verification calls. Estimated charges were $0.304304, including $0.076058 for verification. One draft was rejected and revised. | Keep verification and repair costs visible. These two observations do not establish typical cost or prove the extra work was worthwhile. [Recorded turns](../results/learning-foundation.json). |
| The first rejection concerned the story connecting the facts. | The verifier flagged an unsupported tracing/evaluation relationship, an uncited legacy-workflow warning, and recommendations stated as documented facts. | Inspect whether each criticism is fair. Distinguish source-backed facts from synthesis, preserve caveats, and test whole-task coverage. A rejection is not automatically proof of a better final answer. |
| A follow-up carries both useful context and additional work. | The second real question retained the first exchange, used five calls and cost an estimated $0.116720. Both turns share a conversation ID. | Preserve the context when reviewing a saved answer. Measure cost per accepted answer only after the owner reviews it; both records remain unreviewed. |
| Most observed token cost was input, with no cache activity. | Across the two turns, provider responses reported 159,592 uncached input tokens and 10,184 output tokens; cache write/read counts were zero. Neither turn repeated an identical tool request. | Efficient tool choice does not eliminate repeated-context costs. A separate cold/warm prompt-caching experiment may be worthwhile before adding more agents. No caching change or savings claim is included in this pass. |
| Weave independently exposes the same usage and estimated charges. | Read back two completed turns, 13 chat spans and three verification-tool spans. Provider response IDs and token totals match the local receipts; Weave's summed chat costs match $0.421024 within floating-point tolerance. | Use the app receipt for immediate orientation and Weave for inspection. Sum child chat charges once; do not add parent aggregates. Both are usage-based estimates, not invoices. |
| Browser selectors can fail even when the product action succeeded. | One check matched both progress and final source-check text; another expected selectbox text that was rendered in an input value. | Resume the existing conversation and correct the assertion. Do not resubmit paid requests merely because the test harness failed. Both original answers were retained exactly once. |
| Usage and implementation provenance have limits. | Independent review found that SDK retries are hidden inside one application call, and individual library records do not yet contain an exact prompt/code fingerprint. | Clarify SDK/provider retry exclusions and record the live check's source hash separately. Per-record implementation versioning remains a documented improvement; no invoice or full historical reproducibility claim. |

For subsequent sessions, record findings in this format: observation, linked evidence, consequence, and correction or next experiment. Keep hypotheses and unimplemented ideas labeled. The [reviewer handoff](REVIEWER_HANDOFF.md) is the entry point for another agent; the [evidence index](../results/README.md) links actual run records.
