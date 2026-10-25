from copy import deepcopy

import pytest

from coreweaving.metrics import MeteredModel, estimate_cost, summarize

MODEL = "claude-sonnet-5-5"


@pytest.mark.parametrize(
    "model, usage",
    [
        ("unknown-model", {"input_tokens": 10, "output_tokens": 1}),
        (MODEL, None),
        (MODEL, {}),
        (MODEL, {"input_tokens": 10}),
        (MODEL, {"input_tokens": None, "output_tokens": 1}),
        (MODEL, {"input_tokens": -1, "output_tokens": 1}),
        (MODEL, {"input_tokens": True, "output_tokens": 1}),
        (MODEL, {"input_tokens": 1, "output_tokens": 1.5}),
        (MODEL, {"input_tokens": 10, "output_tokens": 1, "service_tier": "priority"}),
    ],
)
def test_unavailable_or_invalid_usage_is_unknown_not_zero(model, usage):
    assert estimate_cost(model, usage) is None


def test_explicit_zero_usage_is_distinct_from_unknown():
    assert estimate_cost(MODEL, {"input_tokens": 0, "output_tokens": 0}) == 0
    assert summarize([], [])["estimated_usd"] is None


def test_cache_tokens_are_separate_categories_and_ttls_have_distinct_prices():
    usage = {
        "input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 2_000_000,
        "cache_creation": {
            "ephemeral_5m_input_tokens": 1_000_000,
            "ephemeral_1h_input_tokens": 1_000_000,
        },
    }
    original = deepcopy(usage)
    assert estimate_cost(MODEL, usage) == pytest.approx(18.6)
    call = {
        "purpose": "planner",
        "usage": usage,
        "estimated_usd": estimate_cost(MODEL, usage),
    }
    receipt = summarize([call], [])
    assert receipt["total_input_tokens"] == 4_000_000
    assert receipt["tokens"]["output_tokens"] == 1_000_000
    assert receipt["estimated_usd"] == pytest.approx(18.6)
    assert usage == original


@pytest.mark.parametrize(
    "cache_creation",
    [
        None,
        {},
        {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0},
        {"ephemeral_5m_input_tokens": -1, "ephemeral_1h_input_tokens": 2},
        {"ephemeral_5m_input_tokens": True, "ephemeral_1h_input_tokens": 0},
        {"ephemeral_5m_input_tokens": "1", "ephemeral_1h_input_tokens": 0},
        {"ephemeral_5m_input_tokens": 0.5, "ephemeral_1h_input_tokens": 0.5},
        [1],
    ],
)
def test_ambiguous_or_invalid_cache_ttl_stays_unpriced(cache_creation):
    usage = {
        "input_tokens": 10,
        "output_tokens": 1,
        "cache_creation_input_tokens": 1,
        "cache_creation": cache_creation,
    }
    assert estimate_cost(MODEL, usage) is None


def test_receipt_preserves_known_subtotal_without_hiding_unknown_requests():
    calls = [
        {
            "purpose": "planner",
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "estimated_usd": 0.0003,
        },
        {"purpose": "verification", "usage": None, "estimated_usd": None},
    ]
    actions = [
        {"tool": "read_page", "input": {"page_id": "a", "section": 1}, "result": {}},
        {"tool": "read_page", "input": {"section": 1, "page_id": "a"}, "result": {}},
        {
            "tool": "read_page",
            "input": {"page_id": "b", "section": 1},
            "result": {"error": "missing"},
        },
        {"tool": "submit_answer", "input": {"answer": "draft"}, "result": {}},
    ]
    receipt = summarize(calls, actions)
    assert receipt["estimated_usd"] is None
    assert receipt["known_estimated_usd"] == pytest.approx(0.0003)
    assert receipt["unpriced_calls"] == 1
    assert receipt["model_calls"] == 2
    assert receipt["by_purpose"]["verification"]["calls"] == 1
    assert receipt["research"]["passage_reads"] == 2
    assert receipt["research"]["distinct_pages_read"] == 1
    assert receipt["research"]["repeated_tool_requests"] == 1
    assert receipt["research"]["drafts_submitted"] == 1


def test_failed_provider_request_is_recorded_once_and_exception_is_preserved():
    class BrokenModel:
        def call(self, **kwargs):
            raise ConnectionError("offline fixture")

    metered = MeteredModel(BrokenModel())
    with pytest.raises(ConnectionError, match="offline fixture"):
        metered.call(model=MODEL, purpose="verification")
    assert len(metered.calls) == 1
    call = metered.calls[0]
    assert call["error_type"] == "ConnectionError"
    assert call["estimated_usd"] is None
    assert call["usage"] is None
    assert call["elapsed_seconds"] >= 0
    assert summarize(metered.calls, [])["estimated_usd"] is None


def test_returned_model_identity_controls_pricing_and_usage_is_retained():
    returned = {
        "model": "unknown-provider-revision",
        "response_id": "fixture-response",
        "content": [],
        "usage": {"input_tokens": 100, "output_tokens": 10},
    }

    class DifferentModel:
        def call(self, **kwargs):
            return returned

    metered = MeteredModel(DifferentModel())
    assert metered.call(model=MODEL, purpose="planner") is returned
    call = metered.calls[0]
    assert call["response_model"] == returned["model"]
    assert call["response_id"] == "fixture-response"
    assert call["usage"] == returned["usage"]
    assert call["estimated_usd"] is None
