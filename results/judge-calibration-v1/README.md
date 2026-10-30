# Judge calibration — owner labels pending

Thirty saved final answers are selected for owner review. **No human labels or agreement measurements exist yet.** Preparation made no model requests. This is an evaluation of the judge, not a new run of the assistant.

**[Open the Weave labeling queue](https://wandb.ai/devfromlll-learning-layer-labs/coreweaving/weave/annotation-queues/01a18b90-8bf6-71cb-8461-af4793288859).** The [setup receipt](queue-setup.json) verifies 30 matching review copies, eight registered fields and zero completed annotations at handoff. Original scorer readback matched 28 records; two historical scorer children were unavailable under their saved parent IDs. Those examples remain in the sample. Local JSON and CSV alternatives with blank labels are in the owner's private preparation folder.

**Browser access limitation:** an anonymous browser reached the queue URL but displayed an unexpected Weave error. The owner's authenticated view has not been checked. A standalone offline labeling page in the private folder supplies the same answers, context, sources and blank fields, with local saving and a JSON download. It sends nothing to Weave; use one labeling path to avoid counting labels twice. [Access observation](browser-access.json)

[Preparation checks](preparation-checks.json) reproduce the selection, verify the original hashes and confirm all 120 quality labels are blank. [Offline page checks](offline-page-checks.json) cover desktop/mobile layout, all 30 questions, source/context access, navigation and a blank-label download; six screenshots were visually reviewed. No judgments were entered to test the page. [Repository checks](../reviewer-gaps-v1/step-1-checks.json): 430 tests, Ruff and whitespace passed. Runtime files remain unchanged.

## What to label

Read the final answer in its conversation context, its expected behavior, and the saved reference and cited passages. Give **pass/fail and a one-line reason for each quality**:

| Quality | Pass | Fail |
| --- | --- | --- |
| Correctness | Facts, API names and code are accurate, with at most minor issues. | A material factual or code error, or an invented feature. |
| Completeness | Addresses the requested parts and necessary caveats in context. | Misses a requested part or a step necessary to carry it out. |
| Grounding | Sources support the material claims; claimed execution matches the saved result. | A material claim lacks support, misuses a citation or claims execution that did not happen. |
| Uncertainty | Handles ambiguity and unsupported premises honestly. | Invents missing context, accepts a false premise or makes an unjustified guarantee. |

Pass corresponds to the original judge's scores 3–4; fail corresponds to 0–2. A necessary pure clarification can pass without citations. Refusing an answerable question does not automatically pass. Accept valid alternative sources, useful brevity and reasonable scope; do not add unrelated requirements. If unsure, leave the item unfinished and note the question for follow-up. Do not use AI to supply the human labels.

Allow roughly an hour, with more time if source checking needs it. Save your own judgments before opening the original scores or earlier reviews. The owner knows this project, so hiding grades does not make this an independent blinded study.

## Selection and provenance

The [protocol](protocol.json) freezes the pool, seed and selection. It contains **140 valid judged records** from runs using rubric 2.3, the same judge instruction text in their recorded commits and `claude-opus-5-5`. Twenty-one records with failed or missing grades are excluded from agreement analysis, not erased or counted as incorrect answers. Older rubric versions, capability comparisons and synthetic controls are outside this defined pool.

The 30 selected units include:

- All **eight judge-recorded failures** in that pool.
- All **13 cases in the current full regression**, including its one failure.
- The earlier hierarchy answer whose passing grade was disputed in AI-assisted review. That review is a reason to inspect it, not a human label.
- Nine further passes, selected with seed `20261030` to balance categories.

The resulting sample has 22 recorded passes and eight failures across seven categories: basic 7, ambiguous 4, adversarial 4, hallucination traps 4, multi-hop 4, multi-turn 4 and code 3. It spans 11 runtime source versions. One unit is a **final evaluated answer with its conversation context**, matching the original judge's unit; the preceding turns are context, not separately graded independent examples.

[Selection](selection.json) records original paths, prediction IDs, trace links and hashes. [Preparation script](../../scripts/experiments/prepare_judge_calibration.py) reproduces the selection without model calls. Original scores stay in their result files; [judge-key.json](judge-key.json) is a comparison key to open **after** labeling. Human working files stay in the owner's private preparation folder outside Git.

## Why the queue contains review copies

The original `QualityJudge.score` inputs contain the candidate answer, conversation, references and assertions together. Readback did not find every historical scorer call using its saved parent ID. Dropping those records would change the frozen sample, so the queue uses explicit `SavedAnswerForHumanReview` copies of all 30 local records. That operation copies text and makes no inference request. It is **not a new agent run**. Each copy records the original path, hashes, prediction ID and Agent conversation link.

The [queue setup script](publish_queue.py) checks available original scorer inputs and grades, records any unavailable originals, and reads back every review copy against the saved payload. It then publishes eight annotation fields and assigns those 30 review calls. It never submits feedback or human labels. Neither original judge grades nor runtime approval flags are included in the copies. Following provenance links can expose previous grades; avoid that until your labels are saved. References are supplied as saved passages, because live documentation pages can change.

## Analysis after the owner labels

Freeze the owner's exported labels and their authorship before looking at disagreements or adapting any judge. For each quality, treat **pass as positive** and report the counts as well as:

- Agreement = (true positives + true negatives) / labeled answers.
- True-positive rate = judge passes / human passes, restricted to the human-pass group.
- True-negative rate = judge fails / human failures, restricted to the human-fail group.
- False accepts (judge pass, human fail) and false rejects (judge fail, human pass), with evidence-based explanations.

Missing labels are excluded with their counts stated. A zero denominator is **not measurable**, never 100%. This failure-enriched development sample does not estimate production error prevalence. One owner's judgment is not reviewer consensus. Four quality labels also do not independently validate every task assertion or deterministic integrity check in the combined case-pass gate.

Only afterward, freeze a different-family judge using the configured CoreWeave Llama model and re-score these same recorded answers. Supply the same question, context, references and rubric; hide the human and original model grades. No agent re-runs. Preserve invalid judgments as ungraded. Compare both judges with the humans and with each other, including counts and disagreement cases. The original writer and judge are both Opus; separate requests do not make them independent model families.

**Stop here for the owner.** Different-family scoring, repeated trials, confidence intervals, feedback-to-dataset demonstration and the remaining review steps have not been run in this work. Later calls must fit their step allowance and the remaining $30 total cap.
