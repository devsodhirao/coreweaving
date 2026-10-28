"""The published scorer must receive intact agent text, not unresolved placeholders."""

import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from weave.flow.llm_structured_model import LLMStructuredCompletionModel
from weave.flow.monitor import Monitor
from weave.scorers.llm_as_a_judge_scorer import LLMAsAJudgeScorer

from coreweaving.signals import REVIEW_REASONS, SIGNAL_DEFINITION, SIGNAL_QUERY, fixture, setup


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
    assert "What does {project} mean?" not in prompt
    assert "{output_messages}" not in prompt
    assert '"value": "needs-review"' in prompt


def evaluate_query(expression, span):
    """Evaluate only the wire operators used here, independently of the builder."""
    operator, value = next(iter(expression.items()))
    if operator == "$literal":
        return value
    if operator == "$getField":
        field, separator, key = value.partition(".")
        return span.get(field, {}).get(key) if separator else span.get(field)
    if operator == "$and":
        return all(evaluate_query(item, span) for item in value)
    if operator == "$or":
        return any(evaluate_query(item, span) for item in value)
    left, right = value
    if operator == "$eq":
        return evaluate_query(left, span) == evaluate_query(right, span)
    assert operator == "$in"
    return evaluate_query(left, span) in [evaluate_query(item, span) for item in right]


@pytest.mark.parametrize(
    "agent,status,reason,eligible",
    [
        ("coreweaving", "UNSET", "none", False),
        ("coreweaving", "OK", "none", False),
        ("coreweaving", "UNSET", None, False),
        ("coreweaving", "UNSET", "unknown", False),
        ("coreweaving", "ERROR", "none", True),
        ("coreweaving", "UNSET", "operation_failed", True),
        ("coreweaving", "UNSET", "limit_exhausted", True),
        ("coreweaving", "UNSET", "incomplete_answer", True),
        ("coreweaving", "UNSET", "uncited_answer", True),
        ("another-agent", "ERROR", "operation_failed", False),
    ],
)
def test_signal_query_gates_on_recorded_state_not_citations_or_quoted_failures(
    agent, status, reason, eligible
):
    # Even an error containing citations stays eligible. Conversely, user/answer
    # prose cannot make a healthy recorded turn eligible by mentioning failure.
    span = {
        "agent_name": agent,
        "status_code": status,
        "custom_attrs_string": {} if reason is None else {"coreweaving.review_reason": reason},
        "output_messages": [
            {
                "role": "assistant",
                "content": 'A hypothetical "provider failed" example. [S1,S2][C1]',
            }
        ],
    }
    monitor = Monitor(scorers=[], op_names=["weave.genai.turn_ended"], query=SIGNAL_QUERY)
    wire_query = monitor.query.model_dump(mode="json", by_alias=True)
    assert evaluate_query(wire_query["$expr"], span) is eligible


def test_setup_preserves_gate_in_the_actual_activated_monitor(monkeypatch):
    activated, flushed = [], []

    def activate(self):
        activated.append(self)
        return SimpleNamespace(uri=lambda: "weave:///fixture/project/object/review:fixture")

    monkeypatch.setattr(Monitor, "activate", activate)
    monkeypatch.setattr(
        "coreweaving.signals.init_weave",
        lambda: SimpleNamespace(flush=lambda: flushed.append(True)),
    )
    monkeypatch.setattr(
        "coreweaving.signals.settings", lambda: SimpleNamespace(project="fixture/project")
    )
    receipt = setup()
    assert len(activated) == 1 and flushed == [True]
    monitor = activated[0]
    assert monitor.op_names == ["weave.genai.turn_ended"]
    assert monitor.sampling_rate == 1
    assert receipt["query"] == SIGNAL_QUERY
    assert receipt["review_reasons"] == list(REVIEW_REASONS)
    assert receipt["eligibility_policy_version"] == 1
    assert len(monitor.scorers) == 1
    assert monitor.scorers[0].scoring_prompt == SIGNAL_DEFINITION


def test_fixture_records_a_real_error_status_and_explicit_synthetic_reason(monkeypatch):
    attributes, errors = {}, []
    turn = SimpleNamespace(set_attributes=attributes.update, record_error=errors.append)
    monkeypatch.setattr(
        "coreweaving.signals.init_weave", lambda: SimpleNamespace(flush=lambda: None)
    )
    monkeypatch.setattr("weave.start_conversation", lambda **kwargs: nullcontext())
    monkeypatch.setattr("weave.start_turn", lambda **kwargs: nullcontext(turn))
    result = fixture()
    assert attributes == {
        "coreweaving.fixture": True,
        "coreweaving.review_reason": "operation_failed",
    }
    assert len(errors) == 1 and isinstance(errors[0], RuntimeError)
    assert "Synthetic fixture" in str(errors[0])
    assert result["expected_signal"] == "needs-review"
    assert "synthetic" in result["purpose"]
    assert turn.output_messages[0].role == "assistant"
