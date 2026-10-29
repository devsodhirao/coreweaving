That function doesn't exist. I checked the Weave Python SDK reference (v0.53.1), and there's no `enable_hallucination_free_mode()` or any other "enable_*" switch among the top-level functions. Calling it would just raise an `AttributeError`.

More fundamentally, no library call can guarantee an agent never hallucinates. Weave doesn't generate or control your model's outputs. It's an observability and evaluation platform for tracking, evaluating, and improving agents and LLM applications. It can help you *detect and measure* hallucinations, not prevent them.

The real feature you're probably thinking of is `HallucinationFreeScorer`. It checks whether your AI system's output includes any hallucinations based on the input data. You install it with `pip install weave[scorers]`, and since the LLM-based scorers integrate with litellm automatically, you set a `model_id` instead of passing an LLM client. Here's how you'd use it in an evaluation:

```python
import asyncio
import weave
from weave.scorers import HallucinationFreeScorer

weave.init("your-team/your-project")

hallucination_scorer = HallucinationFreeScorer(
    model_id="openai/gpt-4o",
    column_map={"context": "input"},  # map "context" to your dataset's column
)

evaluation = weave.Evaluation(dataset=dataset, scorers=[hallucination_scorer])
result = asyncio.run(evaluation.evaluate(model))
print(result)
```

The scorer's `score` method expects an input column named `context`; if your dataset uses a different name, use `column_map` to point it at the right column. You can also customize its `system_prompt` and `user_prompt` fields to define what "hallucination" means for your use case. The output tells you how often hallucinations were flagged, something like a `has_hallucination` entry with a true count and true fraction.

To watch live agent traffic rather than a fixed dataset, the SDK has a `Monitor` class. It sets up a monitor to score incoming calls automatically, with fields for a sampling rate, the op names to watch, and a list of scorers, and you turn it on by calling `activate()`.

```python
monitor = weave.Monitor(
    name="hallucination-monitor",
    sampling_rate=1.0,
    op_names=["my_agent_op"],
    scorers=[hallucination_scorer],
)
monitor.activate()
```

Keep in mind that this scorer is itself an LLM judge, so it can miss hallucinations or flag correct answers. Treat it as a measurement tool. To actually reduce hallucinations, the usual levers are grounding the agent in retrieved sources, letting it say "I don't know," and rerunning evals like the one above whenever you change prompts or models.