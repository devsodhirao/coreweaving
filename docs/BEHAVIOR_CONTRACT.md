# Permissions, memory and answer release

The assistant answers Weave documentation questions through four named tools. It has no account-administration, deployment, arbitrary browsing or host-file tool. Prompts describe its purpose; runtime dispatch and container controls enforce its capabilities.

## One release path

Verification contract **6** uses one writer loop and one auditor. The auditor sees the original question, retained dialogue, draft, relevant read passages and research actions. It checks every material claim and requested part, returning only `passed`, blocking `issues` and `missing_parts`. It reports exceptions instead of repeating supported claims or code quotations. This reduces reporting work; it does not reduce the intended factual checks.

Before that call, citation contract **3** checks rendered Markdown markers against declared, read evidence; recognized Python fences must parse. The runtime rejects malformed/truncated verdicts, false verdicts, blocking issues and full answers with reported missing parts. The auditor is responsible for identifying unsupported or partly supported claims and code defects. There is no positive-claim inventory or exact-quotation gate. Structural checks surround a fallible semantic judgment; they cannot detect an error the auditor overlooks.

The writer receives feedback and can research or revise within ten writer calls, eighteen research dispatches and two repairs. The last writer call permits submission only. A supported partial answer is authored as `kind=insufficient`, states its limitations and retains nonempty `missing_parts`; it goes through the same auditor. It is not a completed task. A necessary clarification may pass without product claims or citations. No terminal judge, extracted answer or unchecked post-audit prose is added.

Modes are **support** and **off**. The app refuses off; it exists for evaluation experiments and records an unchecked result. The configured offline judge never participates in answer release. The pre-change writer diagnostic is inconclusive. Validation of this compact audit follows the [essence protocol](../results/essence-v1/protocol.md); historical results retain their earlier policies.

## Given / when / then

| Given and when | Required behavior | Boundary |
| --- | --- | --- |
| A model asks for an unknown tool or extra arguments | Dispatch rejects it. | Retrieved text cannot grant capabilities; topic adherence still depends on the model. |
| Search finds a promising section | Read it before citing it. | Search hits, outlines and outgoing links are navigation only. |
| A draft uses unknown, undeclared or disguised citations | Demand repair before model auditing. | Correct IDs do not prove the attached claim. |
| A Python fence is invalid | Parsing rejects the draft. | Valid syntax is not API compatibility or execution. |
| A claim lacks support or a full answer drops a requested part | The auditor should identify the defect; a reported issue or missing part blocks the full answer. | This is a semantic expectation, not a deterministic guarantee. |
| A scoped answer synthesizes supported premises | Accept it without demanding an exact combined quotation or unrelated optional details. | A labeled inference still needs support and cannot invent an automatic integration. |
| Evidence supports only part of the answer | Submit an explicitly limited partial answer for ordinary verification. | Supported fragments are not whole-task completion. |
| A verdict is malformed or a response truncated | Release no unchecked draft and execute no truncated call. | One fresh planner retry uses the next existing slot, not an expanded budget. |
| The user asks a follow-up | Send retained dialogue and preserve original citation evidence. | Trace grouping is not model memory. |
| Streamlit reruns during a turn | The worker continues; completion is consumed once. | Process restart can lose the turn/session. |
| A turn ends | Record outcome, calls, usage and review reason. | Export success, verification and usefulness are separate observations. |

Fixtures in [test_agent.py](../tests/test_agent.py), [test_app.py](../tests/test_app.py) and [test_evaluate.py](../tests/test_evaluate.py) test mechanics with controlled outputs. The [frozen auditor controls](../results/essence-v1/auditor-controls.json) also require accepting a supported recorded draft and scoped synthesis, while rejecting an invented API, a missing requested part and a false claim in a partial answer. Malformed model output is a delivery failure, not evidence of semantic rejection. These selected controls are not a general accuracy estimate. Later captured-answer controls missed the targeted semantic defects; the [current validation](../results/essence-v2/README.md) preserves those limits and the browser check blocked by account funding.

## Data and execution boundaries

| Surface | Enforced behavior | Limit |
| --- | --- | --- |
| Documentation | Resolve page IDs through the locked local corpus. | One snapshot; no arbitrary URL or host-file reads. |
| Python | Non-root Docker, no network/host mounts/injected credentials, read-only root and resource/time/output limits. | Standard library only; neither SDK validation nor a general security guarantee. |
| Credentials | Mask configured secrets and recognized tokens; handle Python literals and serialized JSON structurally. | Unknown/constructed/encoded secrets and general PII can escape. Use public inputs in the public demo project. |
| Telemetry | Encode reference-like literals on logging copies; preserve real SDK references and dataset-row identity. | This is not redaction or rewriting of published data/provider inputs. |
| Chat Markdown | Render images as escaped alt text; disable raw HTML/JavaScript. | Ordinary user-followed links still navigate. |
| Provider connections | Use configured Anthropic and Weave endpoints. | Permitted payloads leave the computer; these are not agent browsing tools. |

Implementations: [config.py](../src/coreweaving/config.py), [telemetry.py](../src/coreweaving/telemetry.py), [sandbox.py](../src/coreweaving/sandbox.py).

## Memory ownership

`Session.history` retains six complete exchanges. `Session.evidence` preserves original passages and execution records; it is not size-capped. Earlier answers supply context, not new documentation authority. New conversation clears working dialogue/evidence; restart loses them. There is no persistent user profile, SQLite answer library or automatic learning from reviews.

Current-session results and Weave's remote records serve inspection. A conversation ID groups traces but does not reload a person's earlier chats. Turning a failure into a dataset requires deliberate selection, references and expected behavior. [Learning loop](LEARNING_LOOP.md)
