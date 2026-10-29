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


def test_explicit_effort_stays_fixed_across_a_conversation(fake_provider):
    model, requests = fake_provider
    for content in ("First question", "Follow-up"):
        model.call(
            model="claude-sonnet-5-5",
            system="Instructions.",
            messages=[{"role": "user", "content": content}],
            tools=[],
            purpose="planner",
            effort="medium",
        )
    assert [request["output_config"] for request in requests] == [{"effort": "medium"}] * 2


def test_literal_reference_text_is_changed_only_on_the_telemetry_copy(fake_provider, monkeypatch):
    from coreweaving.telemetry import LITERAL_PREFIX

    model, requests = fake_provider
    text = "weave:/// URI ref weave.init required"
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("literal-reference-test")
    monkeypatch.setattr(
        "weave.conversation.conversation.otel_trace.get_tracer", lambda *a, **k: tracer
    )
    try:
        model.call(
            model="claude-sonnet-5-5",
            system="Instructions.",
            messages=[{"role": "user", "content": text}],
            tools=[],
            purpose="planner",
        )
        assert requests[0]["messages"][0]["content"] == text
        attributes = str(dict(exporter.get_finished_spans()[0].attributes))
        assert LITERAL_PREFIX + text in attributes
    finally:
        provider.shutdown()


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


def test_provider_and_agent_span_payloads_are_sanitized_before_export(fake_provider, monkeypatch):
    import json

    secret = "synthetic-configured-secret-12345"
    monkeypatch.setenv("WANDB_API_KEY", secret)
    model, requests = fake_provider
    original_create = model.client.messages.create

    def create(**kwargs):
        result = original_create(**kwargs)
        return result.model_copy(
            update={"content": [result.content[0].model_copy(update={"text": secret})]}
        )

    model.client.messages.create = create
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("security-fixture")
    monkeypatch.setattr(
        "weave.conversation.conversation.otel_trace.get_tracer", lambda *a, **k: tracer
    )
    try:
        result = model.call(
            model="claude-sonnet-5-5",
            system="Stable instructions.",
            messages=[{"role": "user", "content": secret}],
            tools=[],
            purpose="planner",
        )
        spans = exporter.get_finished_spans()
        assert spans
        assert secret not in json.dumps([requests, result, [dict(s.attributes) for s in spans]])
        assert "[REDACTED_SECRET]" in requests[0]["messages"][0]["content"]
    finally:
        provider.shutdown()


def test_provider_exception_is_sanitized_before_context_manager_records_it(
    fake_provider, monkeypatch
):
    secret = "synthetic-configured-secret-12345"
    monkeypatch.setenv("WANDB_API_KEY", secret)
    model, _ = fake_provider

    def fail(**kwargs):
        raise ConnectionError("Request contained " + secret)

    model.client.messages.create = fail
    with pytest.raises(RuntimeError) as error:
        model.call(
            model="claude-sonnet-5-5",
            system="Stable instructions.",
            messages=[],
            tools=[],
            purpose="planner",
        )
    assert secret not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize("writes,reads", [(None, None), (0, 0), (91, 1693)])
def test_trace_input_includes_cache_but_provider_receipt_stays_native(
    fake_provider, monkeypatch, writes, reads
):
    model, _ = fake_provider
    original_create = model.client.messages.create

    def create(**kwargs):
        response = original_create(**kwargs)
        return response.model_copy(
            update={
                "usage": response.usage.model_copy(
                    update={
                        "cache_creation_input_tokens": writes,
                        "cache_read_input_tokens": reads,
                    }
                )
            }
        )

    model.client.messages.create = create
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("cache-accounting-fixture")
    monkeypatch.setattr(
        "weave.conversation.conversation.otel_trace.get_tracer", lambda *a, **k: tracer
    )
    try:
        result = model.call(
            model="claude-sonnet-5-5",
            system="Stable instructions.",
            messages=[{"role": "user", "content": "Question"}],
            tools=[],
            purpose="planner",
        )
        chat = next(s for s in exporter.get_finished_spans() if s.name.startswith("chat "))
        assert chat.attributes["gen_ai.usage.input_tokens"] == 12 + (writes or 0) + (reads or 0)
        assert chat.attributes["gen_ai.usage.output_tokens"] == 3
        assert result["usage"]["input_tokens"] == 12
        assert result["usage"]["cache_creation_input_tokens"] == writes
        assert result["usage"]["cache_read_input_tokens"] == reads
    finally:
        provider.shutdown()
