# Completed AI review of the 30 saved answers

At the owner's request, Codex reviewed and filled **120 AI judgments across 30 saved final answers**. These are explicitly AI labels. The owner's JSON, CSV, browser form and Weave human-labeling queue were not filled or replaced. **Human agreement remains unmeasured.**

The review finds **21/30 answers passing all four qualities** and **9/30 with a failed quality**. Five of those nine depend on a strict checklist or source-policy interpretation, identified below. This deliberately selected sample includes older failures across 11 runtime versions. These counts are neither current-app accuracy nor a new regression score. The existing presentation headline remains its original **12/13 cases, 47/48 assertions**.

[Filled judgments and exact evidence](review.json) · [Reproducible evidence checks](evidence-checks.json) · [AI-to-AI comparison](comparison.json)

The private preparation folder contains a completed browser review page with the original answers, all four judgments, reasons, exact excerpts and full saved passages. It also provides an AI-only JSON download. It writes no human labels and sends no annotations to Weave.

[Browser checks](browser-checks.json) cover 1440×1000 and 390×844 viewports: all 30 answers, 120 judgments, 111 quote cards, navigation and the AI-only download match the saved review. Eight screenshots were viewed. No markup errors, broken local references, horizontal overflow or browser errors were found. Hosted trace links were not exercised.

## Findings worth discussing

| Saved answer | Failed quality | Finding | Interpretation |
| --- | --- | --- | --- |
| [J09](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/953adfbf-76f1-417d-abd5-555e15c635c7) | Grounding | The monitoring clarification adds product-specific alternatives with zero read/cited sources. | Clear source-policy miss; a pure question needs no citation. |
| [J10](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/7435462d-c841-4d74-a4cb-1e196310d062) | Completeness | A short list of supported facts leaves the turn/LLM/tool explanation unfinished. | Supported fragments do not complete the requested explanation. |
| [J11](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/03a59c86-2c73-4bb0-93aa-4778303383ec), [J15](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/760676bc-213f-4648-87bb-0943aab851d0) | Completeness | Initialization answers omit authentication and agent-exporter setup. | Checklist-sensitive: useful answers to the literal project-string question, incomplete against the broader frozen requirement. |
| [J16](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/0a4a1940-c590-4560-a811-dd53d9a1dfa3) | Completeness | Lists LLM/tool concepts without explaining how they sit inside turns. | Checklist-sensitive: the central yes/no question and a usable route forward are answered. |
| [J17](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/23268361-4cf5-4714-892c-b0a063915a52) | Completeness | The usage follow-up returns only a research-limit message. | Clear failure to answer. Honest stopping does not make it useful. |
| [J21](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/5b47d94e-4df3-476e-ae04-736d800e746e) | Grounding | Describes Signals/monitors as automated checks without a source. | Borderline source-policy interpretation; J18's noun-only clarification menu passes. |
| [J26](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/d24cdbdd-2fe8-4fcc-8394-49ddf0bbaaa4) | Completeness | Omits conversation-ID reuse and the entire custom-Signal procedure. | Clear omission of explicit user requests. |
| [J27](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/agents/conversations/0cbc4f76-56df-49e9-8f83-5a3168d44c43) | Completeness | Does not explain tool-span recording. | Checklist-sensitive: the frozen assertion requires it, but the literal question does not explicitly mention tools. |

The positive examples also have evidence. J03/J20/J22 retain actual Python outputs of `True, False, True` with mean `0.6666666666666666`. All three calculations were reproduced in isolated local Python processes. J06 correctly separates model-input preprocessing from scorer column mapping. J12 accounts for Anthropic cache tokens in the input total. No live SDK or model-provider example was executed during this review.

## What the checks prove

- **30/30 inputs** match the original records, datasets and saved content hashes.
- **111/111 quoted excerpts** match their exact saved fields and offsets.
- **205/205 document/reference occurrences** match the locked snapshot, allowing the application's recorded credential masking. Repeated passages count as separate occurrences.
- **15 Python blocks** parse. **Three plain-Python replays** reproduce their saved outputs; two share the same code.
- The original scores, submission tag and runtime are preserved. Repository checks are recorded in [local-checks.json](local-checks.json).

These checks establish identity, exact quotations, syntax and the three arithmetic outputs. They do not prove every semantic judgment correct or establish SDK compatibility. To reproduce the offline checks without changing the frozen receipt:

```bash
uv run python results/judge-calibration-v1/ai-review-v1/check_review.py --output /tmp/coreweaving-ai-review-checks.json
```

The script refuses an existing output path. It calls no provider, initializes no Weave client and submits no annotations.

## Comparison with the original grader

The review was saved and hashed before opening `judge-key.json`. This was **not blinded**: the session already contained historical results and known defects. The original writer and grader use Opus; this is an interactive Codex review, not the planned fixed-prompt Llama experiment. No exact reviewer backend-model ID was available.

| Quality | Matching judgments / reviewed answers |
| --- | ---: |
| Correctness | 29/30 |
| Completeness | 28/30 |
| Grounding | 29/30 |
| Uncertainty | 26/30 |

That is **112/120 matching quality labels**, with eight differences across six answers. This is AI-to-AI agreement, not accuracy or human validation. [Every disagreement and its explanation](comparison.json)

The disagreements expose rubric interpretation as well as possible grading misses. For J17, both reviewers reject the answer overall: the original penalizes absent content across several qualities, while this review isolates non-delivery under completeness and accepts the honest stop message. The rubric's “0 absent/wrong” and separate honesty criterion leave room for that disagreement. J16/J27 raise a different question: how strictly should the grader enforce detail that the checklist demands but the literal question does not? Neither issue is settled by quoting an agreement percentage.

No original grade, rubric or assertion was changed. Seeing these AI judgments means any later owner review is informed by them; it must not be presented as blinded human calibration.

## Cost and remaining work

**New evaluation API requests: 0. New experiment API spend: $0.** The $30 allowance remains intact; interactive coding-session usage is outside that ledger. The owner-labeling files remain blank. Human agreement, the configured Llama comparison and the remaining evaluation-gap experiments are still open.
