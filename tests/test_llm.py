from copy import deepcopy
from types import SimpleNamespace

import pytest
import weave
from anthropic.types import Message
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from coreweaving.budget import BudgetExceeded, model_budget
from coreweaving.llm import LanguageModel


@pytest.fixture
def fake_provider():
    requests = []
    model = LanguageModel.__new__(LanguageModel)

    def create(**kwargs):
        requests.append(deepcopy(kwargs))
        return Message.model_validate(
            {
                "id": "fixture-response",
                "type": "message",
                "role": "assistant",
                "model": "claude-sonnet-5-5",
                "content": [{"type": "text", "text": "A fixture response."}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 12, "output_tokens": 3},
            }
        )

    model.retry_options = []

    def with_options(**options):
        model.retry_options.append(options)
        return model.client

    model.client = SimpleNamespace(
        messages=SimpleNamespace(create=create), with_options=with_options
    )
    return model, requests


@pytest.mark.parametrize("cache_enabled", [True, False])
def test_cache_request_fields_are_explicit_and_do_not_change_effort(fake_provider, cache_enabled):
    model, requests = fake_provider
    messages = [{"role": "user", "content": "Read this question."}]
    tools = [{"name": "record_verdict", "input_schema": {"type": "object"}}]
    original = deepcopy((messages, tools))
    output = model.call(
        model="claude-sonnet-5-5",
        system="Stable instructions.",
        messages=messages,
        tools=tools,
        purpose="verification",
        required_tool="record_verdict",
        cache_enabled=cache_enabled,
    )
    request = requests[0]
    expected_system = "Stable instructions.\nReturn your result by calling record_verdict; do not answer in prose."
    if cache_enabled:
        assert request["cache_control"] == {"type": "ephemeral"}
        assert request["system"] == [
            {
                "type": "text",
                "text": expected_system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    else:
        assert "cache_control" not in request
        assert request["system"] == expected_system
    assert "output_config" not in request
    assert "thinking" not in request
    assert "tool_choice" not in request
    assert (messages, tools) == original
    assert output["response_id"] == "fixture-response"
    assert output["usage"]["input_tokens"] == 12


def test_growing_dialogue_preserves_system_prefix(fake_provider):
    model, requests = fake_provider
    messages = [{"role": "user", "content": "First question."}]
    for suffix in ([], [{"role": "assistant", "content": "First answer."}]):
        model.call(
            model="claude-sonnet-5-5",
            system="Stable instructions.",
            messages=messages + suffix,
            tools=[],
            purpose="planner",
        )
    assert requests[0]["system"] == requests[1]["system"]
    assert requests[0]["messages"] == requests[1]["messages"][:1]
    # Request markers make caching eligible; they do not establish a cache hit.
    assert all(request["cache_control"] == {"type": "ephemeral"} for request in requests)


def test_active_budget_disables_sdk_retries_and_charges_returned_usage_once(fake_provider):
    model, requests = fake_provider
    with model_budget(1) as budget:
        model.call(
            model="claude-sonnet-5-5",
            system="A stable prompt.",
            messages=[{"role": "user", "content": "Question"}],
            tools=[],
            purpose="verification",
            max_tokens=100,
        )
    receipt = budget.snapshot()
    assert model.retry_options == [{"max_retries": 0}]
    assert len(requests) == 1
    assert len(receipt["calls"]) == 1
    assert receipt["calls"][0]["purpose"] == "verification"
    assert receipt["calls"][0]["response_id"] == "fixture-response"
    assert receipt["estimated_usd"] == pytest.approx(0.000054)
    assert receipt["reserved_usd"] == 0


def test_budget_rejection_makes_no_provider_request(fake_provider):
    model, requests = fake_provider
    with model_budget(0.000001), pytest.raises(BudgetExceeded):
        model.call(
            model="claude-sonnet-5-5",
            system="A stable prompt.",
            messages=[{"role": "user", "content": "Question"}],
            tools=[],
            purpose="planner",
        )
    assert requests == []
    assert model.retry_options == []


def test_verifier_chat_is_a_child_of_subagent_not_turn(fake_provider, monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("coreweaving-local-test")
    monkeypatch.setattr(
        "weave.conversation.conversation.otel_trace.get_tracer", lambda *args, **kwargs: tracer
    )
    model, _ = fake_provider
    try:
        with weave.start_conversation(
            agent_name="fixture", attributes={"eval.prediction_id": "fixture-prediction"}
        ):
            with weave.start_turn(user_message="Question"):
                with weave.start_subagent(name="source_verifier") as verifier:
                    model.call(
                        model="claude-sonnet-5-5",
                        system="Verify the evidence.",
                        messages=[{"role": "user", "content": "Draft"}],
                        tools=[],
                        purpose="verification",
                        span_parent=verifier,
                    )
        spans = exporter.get_finished_spans()
        subagent = next(span for span in spans if span.name == "invoke_agent source_verifier")
        chat = next(span for span in spans if span.name.startswith("chat "))
        assert chat.parent.span_id == subagent.context.span_id
        assert chat.context.trace_id == subagent.context.trace_id
        assert chat.attributes["eval.prediction_id"] == "fixture-prediction"
        assert chat.attributes["coreweaving.purpose"] == "verification"
    finally:
        provider.shutdown()
