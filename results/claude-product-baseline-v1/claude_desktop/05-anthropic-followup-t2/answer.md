The key is one `llm.record(...)` call inside each `start_llm` block, with Anthropic's usage numbers adjusted to match what Weave expects. Weave shows token counts from the usage you record and computes cost from that usage plus the model id. If either is incomplete or unpriceable, you'll see `0 in / 0 out` or `Cost -` even when the rest of the trace looks fine.

**Mapping Anthropic's fields to Weave's**

`weave.Usage` has five fields: `input_tokens`, `output_tokens`, `reasoning_tokens`, `cache_creation_input_tokens`, and `cache_read_input_tokens`. The catch is that the two APIs define "input" differently. Anthropic's `input_tokens` counts only the uncached part of the prompt, but Weave's `input_tokens` must be the total input, including cached tokens. Weave prices cache reads and writes at their own rates and subtracts them from that total, so you pass the cache fields in addition to a total that already includes them.

| Weave `Usage` field | What to pass from `resp.usage` |
|---|---|
| `input_tokens` | `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` |
| `output_tokens` | `output_tokens` |
| `cache_read_input_tokens` | `cache_read_input_tokens` |
| `cache_creation_input_tokens` | `cache_creation_input_tokens` |

Here's an example of why the sum matters. Suppose Anthropic reports 120 uncached input tokens, 9,800 cache-read tokens, and 350 output tokens. You'd pass `input_tokens=9920` and `cache_read_input_tokens=9800`. Weave then charges 9,800 tokens at the cache-read rate and the remaining 120 at the normal input rate. If you passed only 120 as the input, subtracting 9,800 cached tokens from it leaves nothing to price. The docs warn about exactly this: with prompt caching, cached tokens often dominate the input, so leaving them out makes usage and cost show up as roughly zero.

**The recording code**

```python
def record_anthropic_usage(llm, resp):
    u = resp.usage
    cache_read = u.cache_read_input_tokens or 0       # can be None
    cache_write = u.cache_creation_input_tokens or 0
    llm.record(
        usage=weave.Usage(
            input_tokens=u.input_tokens + cache_read + cache_write,  # total
            output_tokens=u.output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_write,
        ),
        response_id=resp.id,
        response_model=resp.model,   # concrete id, so cost can be looked up
    )

with weave.start_llm(model=MODEL, provider_name="anthropic") as llm:
    resp = client.messages.create(...)
    llm.output(text)
    record_anthropic_usage(llm, resp)   # must run before the block exits
```

Three details in this code matter for cost:

1. **Use the model id from the response.** Cost is looked up by model. Weave uses `response_model` first and falls back to the `model` you passed to `start_llm`. An alias isn't priceable, so pass `resp.model`.
2. **Record before the block closes.** Set the usage and other response fields while the `llm` object is still open, i.e., inside the `with` block.
3. **Guard against `None`.** The `or 0` handles responses where Anthropic leaves the cache fields as `None`. Without it, adding them would raise a `TypeError`. This is my own defensive addition; the docs' example adds the fields directly.

`record()` only applies the arguments you actually pass, so you can call it once for usage and again later for messages without overwriting anything.

**Two Anthropic-specific notes (from Anthropic's API, not the Weave docs)**

If you stream, Anthropic sends usage in pieces across stream events. The simplest fix is `client.messages.stream(...)` and recording from `stream.get_final_message()`, which has the complete usage. And if you use extended thinking, Anthropic includes thinking tokens in `output_tokens` rather than reporting them separately, so I'd leave `reasoning_tokens` unset to avoid counting them twice. The Weave docs don't say how that field is priced.

**Input and output messages**

If you also meant recording the message content, that's separate from cost. `record()` also accepts `input_messages` and `output_messages`, and the `Message` class has helpers like `Message.user(...)`, `Message.assistant(text, tool_calls=...)`, and `Message.tool_result(call_id, output)`. These fill in the chat view but don't affect pricing.

**Checking it worked**

Open a conversation in the Agents view. Each `chat` span should show token counts, latency, and model. If tokens show as zero, the usage is wrong (usually missing cache tokens). If tokens look right but cost shows `Cost -`, the model id isn't priceable, so check that `response_model` is set.