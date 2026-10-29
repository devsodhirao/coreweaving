"""Preserve literal text at Weave's telemetry serialization boundary.

Weave 0.54 interprets ref-shaped string leaves, including strings inside JSON,
as references. Its Conversation fields accept strings rather than a literal
wrapper. Prefix ambiguous application text on a logging copy so it remains
readable without being resolved as a reference. Never use these helpers for
provider requests, tool execution, evidence storage, or the returned answer.

Typed SDK reference objects pass through unchanged. SDK-generated reference
metadata is serialized after this boundary and retains its normal behavior.
"""

import json
from typing import Any

LITERAL_PREFIX = "[coreweaving literal] "
REF_PREFIXES = ("weave://", "weave-trace-internal://")


def trace_text(text: str) -> str:
    """Escape a literal once; preserve its exact bytes after removing the prefix.

    JSON text is protected as one string, preserving its spacing and escaping.
    An existing marker is escaped too, so original text cannot masquerade as an
    encoded value. Call once at the boundary, not on already prepared telemetry.
    """
    if text.startswith((LITERAL_PREFIX, *REF_PREFIXES)):
        return LITERAL_PREFIX + text
    if any(prefix in text for prefix in REF_PREFIXES):
        try:
            json.loads(text)
        except ValueError:
            pass
        except RecursionError:
            # Deep JSON is still literal text; do not make logging fail on it.
            return LITERAL_PREFIX + text
        else:
            return LITERAL_PREFIX + text
    return text


def trace_value(value: Any) -> Any:
    """Copy JSON containers and escape literal leaves, preserving typed objects.

    Suitable for weave.init's client-wide postprocess_inputs/postprocess_output.
    This does not redact secrets; retain the application's existing redaction.
    """
    if isinstance(value, str):
        return trace_text(value)
    if isinstance(value, dict):
        return {key: trace_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [trace_value(item) for item in value]
    return value


def trace_json(value: Any) -> str:
    """Serialize a JSON-compatible telemetry copy for tool arguments/results."""
    return json.dumps(trace_value(value))


def restore_trace_value(value: Any) -> Any:
    """Undo one boundary encoding on readback, leaving real SDK refs untouched.

    For trace_json, first json.loads the stored field, then call this helper.
    Only decode values known to have used this codec; the marker is not an
    authorization or evidence-trust signal.
    """
    if isinstance(value, str):
        return value.removeprefix(LITERAL_PREFIX)
    if isinstance(value, dict):
        return {key: restore_trace_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [restore_trace_value(item) for item in value]
    return value
