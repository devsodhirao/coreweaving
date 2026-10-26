import asyncio

import pytest

from coreweaving.budget import BudgetExceeded, current_budget, model_budget

REQUEST = dict(
    model="claude-sonnet-5-5",
    system="test",
    messages=[{"role": "user", "content": "test"}],
    tools=[],
    max_tokens=100,
)


def test_reservations_prevent_concurrent_overspend_and_release():
    with model_budget(0.02) as budget:
        with budget.reserve(**REQUEST) as ticket:
            with pytest.raises(BudgetExceeded):
                budget.reserve(**REQUEST)
            ticket.complete(REQUEST["model"], {"input_tokens": 100, "output_tokens": 10}, "r1")
        assert budget.snapshot()["reserved_usd"] == 0
        assert budget.snapshot()["estimated_usd"] == pytest.approx(0.0003)
        with budget.reserve(**REQUEST) as ticket:
            ticket.complete(REQUEST["model"], {"input_tokens": 100, "output_tokens": 0}, "r2")
        assert len(budget.snapshot()["calls"]) == 2


def test_unknown_usage_and_errors_stop_future_calls():
    with model_budget(1) as budget:
        with budget.reserve(**REQUEST) as ticket:
            ticket.complete(REQUEST["model"], {})
        with pytest.raises(BudgetExceeded):
            budget.reserve(**REQUEST)
        assert budget.snapshot()["estimated_usd"] is None
        assert budget.snapshot()["known_estimated_usd"] == 0
        assert budget.snapshot()["unpriced_calls"] == 1
        assert budget.snapshot()["remaining_usd"] is None
        assert budget.snapshot()["calls"][0]["estimated_usd"] is None
    with model_budget(1) as budget:
        with pytest.raises(TimeoutError), budget.reserve(**REQUEST):
            raise TimeoutError()
        assert budget.snapshot()["reserved_usd"] == 0
        with pytest.raises(BudgetExceeded):
            budget.reserve(**REQUEST)


def test_budget_context_propagates_to_thread_and_nested_runs_share_it():
    async def check():
        return await asyncio.to_thread(current_budget)

    with model_budget(1) as budget:
        assert asyncio.run(check()) is budget
        with model_budget(1) as nested:
            assert nested is budget
        with pytest.raises(ValueError), model_budget(0.5):
            pass
    assert current_budget() is None


def test_unknown_model_and_small_budget_block_before_request():
    with model_budget(0.001) as budget:
        with pytest.raises(BudgetExceeded):
            budget.reserve(**REQUEST)
        with pytest.raises(BudgetExceeded):
            budget.reserve(**{**REQUEST, "model": "unknown"})
        assert budget.snapshot()["calls"] == []
