The docs.wandb.ai/weave link now redirects to the CoreWeave-hosted Weave docs, and they cover your case directly. Since you aren't using a supported agent SDK, you're in the "custom agents" path. If your agent isn't built with one of the supported SDKs, or it already emits OpenTelemetry spans, you use the Weave SDK directly. Autopatching won't figure out your loop's structure for you, so you add a few explicit spans.

**The structure to follow**

Weave uses four nested concepts, and they map neatly onto a hand-written loop. A conversation groups turns; a turn is one user message and the agent's complete response (an `invoke_agent` span); an LLM call is one call to a model API (a `chat` span); and a tool call is one tool execution triggered by an LLM response (an `execute_tool` span). In Python, all four functions work as context managers (`with weave.start_*(...) as obj:`), and on exit they end the span and flush attributes, including on exceptions.

For your loop, that means one `start_turn` per user message, one `start_llm` per iteration of the loop (each `messages.create` call), and one `start_tool` per `tool_use` block. The docs' quickstart uses a fixed "call LLM, run tools, call LLM again" shape with OpenAI. A real loop that keeps going until `stop_reason` isn't `tool_use` just opens a new `start_llm` span each time around.

**An Anthropic version of the loop**

```python
import json
import anthropic
import weave

weave.init("your-team/your-project")
client = anthropic.Anthropic()
MODEL = "claude-..."  # a concrete model id

def record_anthropic_usage(llm, resp):
    u = resp.usage
    cache_read = u.cache_read_input_tokens or 0      # guard against None
    cache_write = u.cache_creation_input_tokens or 0
    llm.record(
        usage=weave.Usage(
            input_tokens=u.input_tokens + cache_read + cache_write,
            output_tokens=u.output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_write,
        ),
        response_id=resp.id,
        response_model=resp.model,
    )

def run_turn(messages, user_text, max_steps=10):
    messages.append({"role": "user", "content": user_text})
    with weave.start_turn(user_message=user_text, model=MODEL):
        for _ in range(max_steps):
            with weave.start_llm(model=MODEL, provider_name="anthropic") as llm:
                resp = client.messages.create(
                    model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
                )
                text = "".join(b.text for b in resp.content if b.type == "text")
                llm.output(text)
                record_anthropic_usage(llm, resp)
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                return text

            results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                with weave.start_tool(
                    name=block.name,
                    arguments=json.dumps(block.input),  # Anthropic gives a dict
                    tool_call_id=block.id,
                ) as tool:
                    tool.result = run_tool(block.name, block.input)
                results.append({"type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool.result})
            messages.append({"role": "user", "content": results})
        raise RuntimeError("Hit max tool steps")

with weave.start_conversation(agent_name="my-agent"):
    history = []
    print(run_turn(history, "What's the weather in Tokyo?"))
```

**Anthropic-specific details that matter**

There are a few things to get right when calling Anthropic. Set the provider yourself: pass `provider_name` explicitly, because Weave doesn't infer it from the model string. Token accounting is the most common mistake. Anthropic reports cached tokens separately from `input_tokens`, so you need to add them back into the total Weave prices against. This matters because for providers with prompt caching, cached tokens routinely dominate the input, so omitting them makes usage and cost render as roughly zero. Always pass `response_model=resp.model`, since an alias is not priceable and renders `Cost -`, so you should pass the concrete id the response returns. Finally, Weave's `arguments` expects a JSON string, so `json.dumps(block.input)`.

**Where tool spans go**

You have a choice about where tool spans attach. A tool span becomes a child of whatever OTel span is active in context, typically the `chat` span of the LLM call that produced the tool call. The reference example runs tools inside the `start_llm` block, which nests them under the call that requested them. The quickstart runs them after the block, as siblings under the turn. My example uses the sibling layout, which keeps each `chat` span's latency limited to the model call. If you'd rather see causality in the tree, move the tool loop inside the `with weave.start_llm(...)` block.

**Conversations across requests**

If your app is a server handling one turn per request, don't keep a conversation open in memory. If you pass a `conversation_id`, it must be stable across the lifetime of the conversation, and you reuse the same ID to add new turns to an existing conversation. So per request you'd do `with weave.start_conversation(agent_name="my-agent", conversation_id=session_id): run_turn(...)`. This works well because each turn starts its own OTel trace, with turns grouped by a shared `conversation_id` rather than a parent span.

**Smaller conveniences**

You don't need to thread span objects through your code. Any function called within a block can call `start_llm()` or `start_tool()` without holding an explicit reference to the parent, and this works across module boundaries as long as the code runs in the same async context. Your tool-dispatch code can therefore open its own `start_tool` span. Instrumentation is also safe to leave in production: all agent tracing functions no-op silently when tracing is disabled or the init call is absent. If message content is sensitive, `start_conversation` takes `include_content=False` to omit message bodies from spans. If you use extended thinking, the reference examples show `llm.think(...)` for recording reasoning on the `chat` span.

Once it's running, traces appear in the Agents tab of your Weave project, where each conversation shows a multi-turn timeline with nested tool calls, token usage, and feedback. The docs also note this workflow is available in CoreWeave Agent Lens, which reads the same trace data, so nothing changes in your code either way.