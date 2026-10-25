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
| Weave returned repeated 502 responses when finishing the initial three-case evaluation's parent Call. | Local per-case outputs and summary survived; nested predictions and judge scores reached Weave. Track remote completion separately and verify the full submission run. Do not treat a flush call as proof of delivery. |
| Publishing a Signal does not establish that it scored any turns. | Emit a labeled negative fixture and inspect backend feedback. Keep monitoring marked pending until real feedback is observed. |

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
