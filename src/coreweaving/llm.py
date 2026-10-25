"""One provider boundary, with complete typed agent spans and bounded retries."""

import json

import anthropic
import weave
from weave.conversation.adapters.anthropic import usage_from_anthropic
from weave.conversation.types import TextPart, ToolCallPart, ToolCallResponsePart


def trace_message(message: dict) -> weave.Message:
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
    ) -> dict:
        if required_tool:
            # Sonnet/Opus 5.5 reject forced tool_choice. Ask for the schema tool
            # and validate its presence and arguments at the application boundary.
            system += f"\nReturn your result by calling {required_tool}; do not answer in prose."
        with weave.start_llm(
            model=model, provider_name="anthropic", system_instructions=[system]
        ) as span:
            span.set_attributes({"coreweaving.purpose": purpose})
            span.input_messages = [trace_message(message) for message in messages]
            span.request_max_tokens = max_tokens
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                tools=tools,
            )
            blocks = [block.model_dump(exclude_none=True) for block in response.content]
            span.record(
                output_messages=[trace_message({"role": "assistant", "content": blocks})],
                usage=usage_from_anthropic(response),
                response_id=response.id,
                response_model=response.model,
                finish_reasons=[response.stop_reason or ""],
            )
            return {
                "content": blocks,
                "stop_reason": response.stop_reason,
                "usage": response.usage.model_dump(),
            }
