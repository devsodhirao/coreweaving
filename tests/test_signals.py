"""The published scorer must receive intact agent text, not unresolved placeholders."""

import json

from weave.flow.llm_structured_model import LLMStructuredCompletionModel
from weave.scorers.llm_as_a_judge_scorer import LLMAsAJudgeScorer

from coreweaving.signals import SIGNAL_DEFINITION


def test_signal_sdk_template_preserves_serialized_message_text(monkeypatch):
    requests = []

    def capture(self, user_input, **kwargs):
        requests.append(user_input)
        return {"scores": []}

    monkeypatch.setattr(LLMStructuredCompletionModel, "predict", capture)
    model = LLMStructuredCompletionModel(llm_model_id="test/no-provider")
    scorer = LLMAsAJudgeScorer(model=model, scoring_prompt=SIGNAL_DEFINITION)
    answer = 'Initialize with weave.init("team/project"). [S12] Example: {"key": "value"}'
    messages = [{"role": "assistant", "content": json.dumps([{"type": "text", "content": answer}])}]
    verdict = scorer.score(
        output="unused by this template",
        agent_name="coreweaving",
        status_code="UNSET",
        status_message="",
        input_messages=[{"role": "user", "content": "What does {project} mean?"}],
        output_messages=messages,
    )
    assert verdict == {"scores": []}
    assert len(requests) == 1
    prompt = requests[0][0]["content"]
    assert str(messages) in prompt
    assert "[S12]" in prompt
    assert "{project}" in prompt
    assert "{output_messages}" not in prompt
    assert '{"scores": []}' in prompt
