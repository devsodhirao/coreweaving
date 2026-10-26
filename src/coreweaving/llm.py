"""One provider boundary, with complete typed agent spans and bounded retries."""

import json

import anthropic
import weave
from weave.conversation.adapters.anthropic import usage_from_anthropic
from weave.conversation.types import TextPart, ToolCallPart, ToolCallResponsePart

from coreweaving.budget import current_budget
from coreweaving.config import redact_sensitive, safe_exception


def trace_message(message: dict) -> weave.Message:
    """Translate provider text/tool blocks without losing tool-call identities."""
    content = message["content"]
    if isinstance(content, str):
        return weave.Message(role=message["role"], content=content)
    parts = []
    for block in content:
        if block["type"] == "text":
            parts.append(TextPart(content=block["text"]))
        elif block["type"] == "tool_use":
            parts.append(
                ToolCallPart(
                    id=block["id"], name=block["name"], arguments=json.dumps(block["input"])
                )
            )
        elif block["type"] == "tool_result":
            parts.append(ToolCallResponsePart(id=block["tool_use_id"], response=block["content"]))
    return weave.Message(role=message["role"], parts=parts)


class LanguageModel:
    """Anthropic transport for the planner/verifier, instrumented exactly once."""

    def __init__(self):
        # Anthropic 2.x also emits native OTel spans. We record each request once
        # ourselves, with full messages and a named purpose, to avoid double usage.
        self.client = anthropic.Anthropic(
            timeout=50.0, max_retries=1, open_telemetry={"traces": False}
        )

    def call(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict],
        tools: list[dict],
        purpose: str,
        required_tool: str | None = None,
        max_tokens: int = 2400,
        cache_enabled: bool = True,
        span_parent=None,
    ) -> dict:
        """Make one request and return raw usage alongside redacted output blocks.

        Explicit subagent parenting preserves verifier ownership in Weave. The
        tracing adapter uses inclusive input counts; cost receipts keep Anthropic's
        original disjoint cache buckets. Experiment budgets disable hidden retries.
        """
        system, messages, tools = redact_sensitive((system, messages, tools))
        if required_tool:
            # Sonnet/Opus 5.5 reject forced tool_choice. Ask for the schema tool
            # and validate its presence and arguments at the application boundary.
            system += f"\nReturn your result by calling {required_tool}; do not answer in prose."
        # The top-level helper pins chats to the current Turn. Delegated audits
        # must explicitly use their SubAgent factory to preserve the parent.
        start_llm = span_parent.start_llm if span_parent is not None else weave.start_llm
        with start_llm(
            model=model, provider_name="anthropic", system_instructions=[system]
        ) as span:
            span.set_attributes(
                {"coreweaving.purpose": purpose, "coreweaving.cache_enabled": cache_enabled}
            )
            span.input_messages = [trace_message(message) for message in messages]
            span.request_max_tokens = max_tokens
            request = dict(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                tools=tools,
            )
            if cache_enabled:
                # The static prefix and growing conversation use independent
                # breakpoints. Actual writes/hits are measured from returned usage.
                request["system"] = [
                    {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
                ]
                request["cache_control"] = {"type": "ephemeral"}
            budget = current_budget()
            try:
                if budget:
                    with budget.reserve(
                        model=model,
                        system=request["system"],
                        messages=messages,
                        tools=tools,
                        max_tokens=max_tokens,
                        purpose=purpose,
                    ) as ticket:
                        response = self.client.with_options(max_retries=0).messages.create(
                            **request
                        )
                        ticket.complete(response.model, response.usage.model_dump(), response.id)
                else:
                    response = self.client.messages.create(**request)
            except Exception as exc:
                if type(exc).__name__ == "BudgetExceeded":
                    raise
                raise safe_exception(exc) from None
            blocks = redact_sensitive(
                [block.model_dump(exclude_none=True) for block in response.content]
            )
            # OTel input includes cache reads/writes. Anthropic's input_tokens
            # excludes both; Weave 0.54's adapter copies that net count unchanged.
            # Normalize the span only; retain raw usage for our cost ledger.
            traced_usage = usage_from_anthropic(response)
            traced_usage.input_tokens += (traced_usage.cache_creation_input_tokens or 0) + (
                traced_usage.cache_read_input_tokens or 0
            )
            span.record(
                output_messages=[trace_message({"role": "assistant", "content": blocks})],
                usage=traced_usage,
                response_id=response.id,
                response_model=response.model,
                finish_reasons=[response.stop_reason or ""],
            )
            return {
                "content": blocks,
                "stop_reason": response.stop_reason,
                "usage": response.usage.model_dump(),
                "model": response.model,
                "response_id": response.id,
            }
