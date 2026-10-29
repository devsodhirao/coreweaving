"""Usage receipts and dated list-price estimates, never an account invoice."""

import json
import time
from collections import Counter

PRICE_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICE_CHECKED_AT = "2026-10-25"
# Standard direct Claude API USD per million tokens. No batch or regional premium.
PRICES = {
    "claude-sonnet-5-5": {"input": 2, "output": 10, "write_5m": 2.5, "write_1h": 4, "read": 0.10},
    "claude-opus-5-5": {"input": 4, "output": 20, "write_5m": 5, "write_1h": 8, "read": 0.20},
}
TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


def estimate_cost(model: str, usage: dict | None) -> float | None:
    """Unknown models, missing usage, or ambiguous cache TTLs stay unpriced."""
    rate = PRICES.get(model)
    if not rate or not isinstance(usage, dict):
        return None
    if any(type(usage.get(k)) is not int for k in ("input_tokens", "output_tokens")):
        return None
    if usage.get("service_tier") not in (None, "standard"):
        return None
    tokens = {key: usage.get(key, 0) or 0 for key in TOKEN_FIELDS}
    if any(type(value) is not int or value < 0 for value in tokens.values()):
        return None
    writes = usage.get("cache_creation")
    if writes is not None and not isinstance(writes, dict):
        return None
    writes = writes or {}
    short = writes.get("ephemeral_5m_input_tokens", 0) or 0
    long = writes.get("ephemeral_1h_input_tokens", 0) or 0
    if any(type(value) is not int or value < 0 for value in (short, long)):
        return None
    if short + long != tokens["cache_creation_input_tokens"]:
        return None
    return round(
        (
            tokens["input_tokens"] * rate["input"]
            + tokens["output_tokens"] * rate["output"]
            + tokens["cache_read_input_tokens"] * rate["read"]
            + short * rate["write_5m"]
            + long * rate["write_1h"]
        )
        / 1_000_000,
        8,
    )


class MeteredModel:
    """Wrap the common call boundary so rejected drafts and verification count."""

    def __init__(self, model):
        self.model = model
        self.calls: list[dict] = []

    def call(self, **kwargs):
        started = time.monotonic()
        record = {
            "purpose": kwargs["purpose"],
            "requested_model": kwargs["model"],
            "effort": kwargs.get("effort") or "provider_default",
            "response_model": None,
            "response_id": None,
            "usage": None,
            "error_type": None,
        }
        try:
            response = self.model.call(**kwargs)
            record.update(
                response_model=response.get("model"),
                response_id=response.get("response_id"),
                usage=response.get("usage"),
            )
            return response
        except Exception as exc:
            record["error_type"] = type(exc).__name__
            raise
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 4)
            record["estimated_usd"] = estimate_cost(
                record["response_model"] or record["requested_model"], record["usage"]
            )
            self.calls.append(record)


def summarize(calls: list[dict], actions: list[dict]) -> dict:
    totals = dict.fromkeys(TOKEN_FIELDS, 0)
    stages = {}
    for call in calls:
        usage = call.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        for key in TOKEN_FIELDS:
            value = usage.get(key, 0)
            if type(value) is int and value >= 0:
                totals[key] += value
        stage = stages.setdefault(call["purpose"], {"calls": 0, "known_estimated_usd": 0.0})
        stage["calls"] += 1
        stage["known_estimated_usd"] += call["estimated_usd"] or 0
    unknown = sum(call["estimated_usd"] is None for call in calls)
    known = round(sum(call["estimated_usd"] or 0 for call in calls), 8)
    counts = Counter(action["tool"] for action in actions)
    reads = [a for a in actions if a["tool"] == "read_page" and "error" not in a["result"]]
    identities = [
        (a["tool"], json.dumps(a["input"], sort_keys=True))
        for a in actions
        if a["tool"] != "submit_answer"
    ]
    return {
        "calls": calls,
        "model_calls": len(calls),
        "tokens": totals,
        "total_input_tokens": sum(totals[k] for k in TOKEN_FIELDS if k != "output_tokens"),
        "estimated_usd": known if calls and not unknown else None,
        "known_estimated_usd": known,
        "unpriced_calls": unknown,
        "by_purpose": stages,
        "research": {
            "searches": counts["search_docs"],
            "passage_reads": len(reads),
            "distinct_pages_read": len({a["input"]["page_id"] for a in reads}),
            "repeated_tool_requests": len(identities) - len(set(identities)),
            "drafts_submitted": counts["submit_answer"],
            "code_runs": counts["run_python"],
        },
        "pricing": {"checked_at": PRICE_CHECKED_AT, "source": PRICE_SOURCE, "rates": PRICES},
        "scope": (
            "Standard Claude API list-price estimate for returned usage, including planning and "
            "verification. Excludes Weave Signals, offline evaluation judges, voice, hosting, "
            "taxes, and any usage not returned after failures or SDK/provider retries. "
            "Calls count application invocations, not every HTTP attempt. This is not an invoice. "
            "Research counts do not measure factual completeness."
        ),
    }
