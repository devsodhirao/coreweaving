"""Offline reproduction of literal/ref ambiguity; no SDK init or remote transport."""

import base64
import hashlib
import importlib.metadata
import inspect
import json
import socket
from pathlib import Path

network_attempts = []


def deny_network(*args, **kwargs):
    network_attempts.append("socket connection attempted")
    raise AssertionError("Network disabled for this probe")


socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network

# Imports intentionally follow the socket guard so this diagnostic cannot connect.
import httpx  # noqa: E402
from weave.conversation.conversation_otel import execute_tool_attributes  # noqa: E402
from weave.trace.serialization.serialize import from_json, to_json  # noqa: E402
from weave.trace.trace_server_converter import universal_ext_to_int_ref_converter  # noqa: E402

queries = [
    "weave:/// URI ref weave.init required",
    "weave:/// URI fully qualified ref weave.init required",
]
resolved_projects = []


def resolve(project):
    resolved_projects.append(project)
    return "internal-project"


def fake_server(request):
    payload = json.loads(request.content)
    try:
        converted = universal_ext_to_int_ref_converter(payload, resolve)
    except Exception as error:
        return httpx.Response(400, json={"reason": str(error), "exception": type(error).__name__})
    return httpx.Response(200, json={"converted": converted})


cases = []
for i, query in enumerate(queries):
    cases.extend(
        [
            (
                f"query{i + 1}_legacy_output",
                {"output": {"actions": [{"input": {"query": query}}]}},
                400,
            ),
            (
                f"query{i + 1}_tool_otel_attributes",
                execute_tool_attributes(
                    tool_name="search_docs", tool_call_arguments=json.dumps({"query": query})
                ),
                400,
            ),
        ]
    )
query = queries[0]
cases.extend(
    [
        ("text_contains_uri_but_does_not_start_with_it", {"query": "Find " + query}, 200),
        ("ordinary_json_encoding_does_not_protect_literal", {"query": json.dumps(query)}, 400),
        ("dictionary_wrapper_does_not_protect_literal", {"literal": {"text": query}}, 400),
        (
            "reversible_base64_telemetry_literal",
            {"literal_utf8_base64": base64.b64encode(query.encode()).decode()},
            200,
        ),
        (
            "canonical_ref_positive_control",
            {"ref": "weave:///entity/project/object/example:version"},
            200,
        ),
        (
            "mixed_batch_one_literal_rejects_whole_payload",
            {"batch": [{"query": "normal"}, {"query": query}]},
            400,
        ),
    ]
)
results = []
with httpx.Client(transport=httpx.MockTransport(fake_server)) as client:
    for name, original, expected in cases:
        serialized = to_json(original, "entity/project", None)
        assert serialized == original, name
        response = client.post("https://offline.invalid/fake-ingest", json=serialized)
        assert response.status_code == expected, (name, response.text)
        results.append(
            {
                "name": name,
                "expected_status": expected,
                "observed_status": response.status_code,
                "wire_payload_unchanged_by_to_json": True,
                "response": response.json(),
            }
        )
readback = []
for query in queries:
    try:
        from_json({"query": query}, "entity/project", None)
    except Exception as error:
        readback.append({"query": query, "exception": type(error).__name__, "message": str(error)})
    else:
        raise AssertionError("Expected prefix-based deserialization failure")
assert network_attempts == []
files = {}
for function in [to_json, universal_ext_to_int_ref_converter, execute_tool_attributes]:
    path = Path(inspect.getfile(function))
    files[path.name] = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "installed_relative_path": str(path).split("/site-packages/", 1)[1],
    }
receipt = {
    "sdk_version": importlib.metadata.version("weave"),
    "status": "offline_mechanism_reproduced",
    "transport": "httpx.MockTransport invoking the installed converter; not a remote server",
    "network_attempts": len(network_attempts),
    "cases": results,
    "readback_heuristic": readback,
    "canonical_positive_resolved_projects": resolved_projects,
    "installed_source": files,
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "scope": "Shows identical error text and recursive failure mechanism in installed0.54.0. Actual remote implementation, batch atomicity and retry behavior are not established by this fake transport.",
}
# Emit evidence only; never overwrite the committed receipt or initialize tracing.
print(json.dumps(receipt, indent=2))
