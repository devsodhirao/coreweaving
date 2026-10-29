"""Actual SDK conversion controls; no tracing initialization or network."""

import json
import socket
from copy import deepcopy

import pytest
import weave
from weave.conversation.conversation_otel import (
    execute_tool_attributes,
    invoke_agent_attributes,
    llm_attributes,
)
from weave.conversation.types import TextPart, ToolCallPart, ToolCallResponsePart
from weave.trace.errors import InvalidExternalRef
from weave.trace.refs import Ref
from weave.trace.serialization.serialize import from_json, to_json
from weave.trace.trace_server_converter import (
    universal_ext_to_int_ref_converter,
    universal_int_to_ext_ref_converter,
)
from weave.trace.vals import WeaveList

from coreweaving.telemetry import (
    LITERAL_PREFIX,
    restore_trace_value,
    trace_json,
    trace_text,
    trace_value,
)

QUERY = "weave:/// URI ref weave.init required"
CANONICAL = "weave:///entity/project/object/example:version"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Telemetry tests must not connect to a server")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def sdk_roundtrip(value):
    """Use the installed converter with local resolvers, not a fake parser."""
    wire = to_json(value, "entity/project", None)
    internal = universal_ext_to_int_ref_converter(wire, lambda _: "project-id")
    external = universal_int_to_ext_ref_converter(internal, lambda _: "entity/project")
    return from_json(deepcopy(external), "entity/project", None)


@pytest.mark.parametrize(
    "text",
    [
        QUERY,
        "weave:/// URI fully qualified ref weave.init required",
        "weave://",
        "weave-trace-internal:///literal-not-a-reference",
        CANONICAL,
        LITERAL_PREFIX + QUERY,
        LITERAL_PREFIX + "ordinary user text",
        json.dumps({"query": QUERY}, indent=3),
        json.dumps(json.dumps({"query": QUERY})),
        json.dumps([{"content": CANONICAL}, {"query": QUERY}]),
    ],
)
def test_literal_text_survives_actual_sdk_serialization_and_readback(text):
    encoded = trace_text(text)
    assert encoded == LITERAL_PREFIX + text
    assert restore_trace_value(sdk_roundtrip(encoded)) == text


@pytest.mark.parametrize(
    "text",
    [
        "Normal question.",
        "Use weave:/// in a fully qualified reference.",
        'Use the literal string "weave:///" in your example.',
        "```python\nref = 'weave:///entity/project/object/example:version'\n```",
        json.dumps({"query": "ordinary text"}),
    ],
)
def test_ordinary_prose_and_code_keep_original_telemetry_bytes(text):
    assert trace_text(text) == text
    assert sdk_roundtrip(trace_text(text)) == text


def test_actual_converter_negative_control_preserved():
    with pytest.raises(InvalidExternalRef, match="Invalid URI"):
        sdk_roundtrip({"query": QUERY})


def test_literal_and_actual_reference_remain_distinct():
    reference = Ref.parse_uri(CANONICAL)
    value = {"literal": CANONICAL, "actual_ref": reference}
    encoded = trace_value(value)
    assert encoded["actual_ref"] is reference
    decoded = restore_trace_value(sdk_roundtrip(encoded))
    assert decoded["literal"] == CANONICAL
    assert isinstance(decoded["literal"], str)
    assert decoded["actual_ref"] == reference
    assert type(decoded["actual_ref"]) is type(reference)


def test_logged_copy_does_not_change_tool_input_evidence_or_original_containers():
    value = {"actions": [{"input": {"query": QUERY}, "result": {"text": CANONICAL}}]}
    original = deepcopy(value)
    encoded = trace_value(value)
    assert value == original
    assert encoded is not value and encoded["actions"] is not value["actions"]
    assert restore_trace_value(sdk_roundtrip(encoded)) == original


def test_weave_container_and_tuple_are_normalized_without_reconstruction():
    wrapped = WeaveList([QUERY, {"text": CANONICAL}], server=None)
    assert restore_trace_value(sdk_roundtrip(trace_value({"items": wrapped}))) == {
        "items": [QUERY, {"text": CANONICAL}]
    }
    assert wrapped[0] == QUERY
    assert restore_trace_value(trace_value((QUERY, 1, None))) == [QUERY, 1, None]


def test_tool_attributes_preserve_exact_arguments_result_and_real_call_identity():
    arguments = {"query": QUERY}
    result = {"snippet": CANONICAL, "nested_json": json.dumps({"literal": QUERY})}
    attributes = execute_tool_attributes(
        tool_name="search_docs",
        tool_call_id="real-provider-id",
        tool_call_arguments=trace_json(arguments),
        tool_call_result=trace_json(result),
    )
    stored = sdk_roundtrip(attributes)
    assert stored["gen_ai.tool.call.id"] == "real-provider-id"
    assert restore_trace_value(json.loads(stored["gen_ai.tool.call.arguments"])) == arguments
    assert restore_trace_value(json.loads(stored["gen_ai.tool.call.result"])) == result


def test_agent_and_model_message_serializers_keep_supported_parts_and_restore_text():
    payload = json.dumps({"candidate": {"answer": QUERY}, "evidence": [CANONICAL]}, indent=2)
    messages = [
        weave.Message(role="user", content=trace_text(payload)),
        weave.Message(
            role="assistant",
            parts=[
                TextPart(content=trace_text(QUERY)),
                ToolCallPart(
                    id="provider-tool-id",
                    name="search_docs",
                    arguments=trace_json({"query": QUERY}),
                ),
            ],
        ),
        weave.Message(
            role="tool",
            parts=[ToolCallResponsePart(id="provider-tool-id", response=trace_text(payload))],
        ),
    ]
    for attributes in (
        invoke_agent_attributes(agent_name="fixture", input_messages=messages),
        llm_attributes(model="fixture-model", input_messages=messages),
    ):
        stored = sdk_roundtrip(attributes)
        parts = json.loads(stored["gen_ai.input.messages"])
        assert restore_trace_value(parts[0]["parts"][0]["content"]) == payload
        assert restore_trace_value(parts[1]["parts"][0]["content"]) == QUERY
        tool = parts[1]["parts"][1]
        assert tool["id"] == "provider-tool-id"
        assert restore_trace_value(json.loads(tool["arguments"])) == {"query": QUERY}
        assert restore_trace_value(parts[2]["parts"][0]["response"]) == payload
