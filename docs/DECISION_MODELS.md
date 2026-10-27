# Faster decisions: Jev and OpenJev

Research assessed on 26 October 2026. **Decision: considered and deferred.** Jev is not needed to meet this brief, and current evidence does not justify adding it. The submitted runtime uses neither Jev nor OpenJev. No provider calls, local deployment or speed measurements were made for this assessment.

## Why this is relevant

Our slow turns involve several sequential planning and verification calls. A decision model could classify evidence without writing an explanation each time. The useful question is whether a cheaper decision can replace an expensive call while preserving useful, supported answers.

TypeSafe Jev returns typed decisions and option probabilities. Its Choice `confidence` rescales the largest probability relative to a uniform distribution; it is derived from the probabilities, not an independent correctness check. TypeSafe recommends setting thresholds using performance on the actual task. A confidence value of 0.9 therefore does not establish that 90% of this app's answers would be correct. [TypeSafe confidence documentation](https://docs.typesafe.ai/confidence)

The September 2026 preprint *JEV-as-a-Judge* studies accepting confident decision-model verdicts and escalating others to a reasoning judge. It reports stronger results when the verdict follows directly from supplied text, and weaker performance where it requires derivation, including code and logic. Style-adversarial pairs and reference-free prose also weaken confidence routing. That makes passage-to-claim checking a plausible experiment here; the paper's results are not measurements of our app. [Paper, revised 9 October](https://arxiv.org/abs/2609.26550)

## Which OpenJev?

There are independent implementations with this name. They should not be treated as TypeSafe's official open model or assumed interchangeable.

| Candidate | What matters for this project |
| --- | --- |
| [razorback16/openjev](https://github.com/razorback16/openjev) | Jev-compatible decision server using DiffusionGemma, with NVIDIA and Apple silicon serving paths. Its entropy-based confidence differs from TypeSafe's top-probability formula, so thresholds do not transfer automatically. Local serving adds hardware and operational work. |
| [openjev/openjev model](https://huggingface.co/openjev/openjev) | A separate option-logit model with its own serving recipe. The model card distinguishes CC BY-NC 4.0 weights from Apache-2.0 helper code. Licensing and deployment need review before product adoption. |

## Why we are not adding it

The submitted run and later replay exposed omitted details, incomplete answers, excessive rejection and an accepted invalid code sketch. A source-support classifier alone cannot establish that the whole question was answered. The latency investigation also found duplicated drafting and serial calls; removing unnecessary work is a simpler first response than introducing another inference service. A classifier would add latency, calibration data requirements, deployment and explanation costs to an already expanded take-home.

We would reconsider only if profiling identifies a repeated, narrow decision that dominates time or cost, simpler improvements are insufficient, and enough labeled examples exist to evaluate a replacement. Faster typed output by itself meets none of those conditions.

## Evaluation requirements if that need emerges

1. **Start beside the existing verifier.** Give the candidate model the same claims and passages. Request supported / contradicted / insufficient-evidence decisions; record them without changing what reaches the user. Keep citation and permission checks mandatory.
2. **Label real failures.** Include missing caveats, supported paraphrases, fabricated APIs, stale/current workflows and context-dependent follow-ups. Label source support and task completeness separately: a supported answer can still be unhelpful.
3. **Calibrate, then test.** Separate question families into development, calibration and untouched test sets. Choose escalation thresholds on calibration data. The reused 13-case suite is too small to validate a reliable confidence threshold.
4. **Measure the whole experience.** Compare unsupported answers released, useful answers withheld, assertion/case passes, escalation rate, median/p95 time to a checked answer and total cost. Count the classifier call itself. An extra serial decision can make the app slower.
5. **Use Weave to explain the result.** Trace the decision model, evidence, probabilities, chosen route and fallback. Compare frozen policies through evaluations; monitor failures after deployment. Weave makes these choices inspectable, but supplies no automatic calibration guarantee.

No experiment is scheduled. If a replacement becomes justified, evaluate one focused decision before changing the whole loop. Routing search versus clarification would require a separate label set. Generative planning, synthesis and code explanation remain necessary. Adoption depends on measured quality and latency, rather than a confidence badge or a vendor benchmark.
