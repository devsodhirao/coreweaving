"""Conservative per-request reservations for bounded experiments, not a billing cap."""

import json
import threading
from contextlib import contextmanager
from contextvars import ContextVar

from coreweaving.metrics import PRICES, estimate_cost

_ACTIVE = ContextVar("coreweaving_model_budget", default=None)


class BudgetExceeded(RuntimeError):
    """No provider request was made because the experiment budget is unavailable."""


class ModelBudget:
    def __init__(self, limit_usd: float):
        if not 0 < limit_usd <= 100:
            raise ValueError("Experiment budget must be greater than zero and at most $100.")
        self.limit_usd = float(limit_usd)
        self.spent = 0.0
        self.reserved = 0.0
        self.calls = []
        self.stopped_reason = None
        self.lock = threading.RLock()

    def reserve(self, *, model, system, messages, tools, max_tokens, purpose="model"):
        rate = PRICES.get(model)
        if rate is None:
            raise BudgetExceeded("No known price for this model; experiment request withheld.")
        # One byte per input token plus provider/tool overhead is intentionally
        # conservative. This is not a provider token count or invoice guarantee.
        payload = json.dumps([system, messages, tools], ensure_ascii=False).encode()
        input_allowance = len(payload) + 4096
        reservation = (
            input_allowance * max(rate["input"], rate["write_5m"]) + max_tokens * rate["output"]
        ) / 1_000_000
        with self.lock:
            if self.stopped_reason:
                raise BudgetExceeded(self.stopped_reason)
            if self.spent + self.reserved + reservation > self.limit_usd:
                raise BudgetExceeded(
                    "Remaining experiment budget cannot cover the next request reservation."
                )
            self.reserved += reservation
        return _Reservation(self, reservation, model, purpose)

    def snapshot(self):
        with self.lock:
            unpriced = sum(call["estimated_usd"] is None for call in self.calls)
            return {
                "limit_usd": self.limit_usd,
                "estimated_usd": None if unpriced else round(self.spent, 8),
                "known_estimated_usd": round(self.spent, 8),
                "unpriced_calls": unpriced,
                "estimate_complete": not unpriced,
                "reserved_usd": round(self.reserved, 8),
                "remaining_usd": None
                if unpriced
                else round(max(0, self.limit_usd - self.spent - self.reserved), 8),
                "stopped_reason": self.stopped_reason,
                "calls": list(self.calls),
                "scope": (
                    "Returned agent and judge usage at dated standard API prices. Conservative "
                    "reservations before requests; SDK retries disabled by experiment adapters. "
                    "Stops on unpriced usage or failed provider calls. Excludes Signals, hosting, "
                    "taxes and unreturned charges. This is not an account billing cap."
                ),
            }


class _Reservation:
    def __init__(self, budget, amount, model, purpose):
        self.budget, self.amount = budget, amount
        self.model, self.purpose = model, purpose
        self.completed = False
        self.closed = False

    def __enter__(self):
        return self

    def complete(self, model, usage, response_id=None):
        if self.completed or self.closed:
            raise RuntimeError("Budget reservation already completed or closed.")
        cost = estimate_cost(model, usage)
        with self.budget.lock:
            self.budget.calls.append(
                {
                    "purpose": self.purpose,
                    "model": model,
                    "response_id": response_id,
                    "usage": usage,
                    "estimated_usd": cost,
                    "reservation_usd": round(self.amount, 8),
                }
            )
            if cost is None:
                self.budget.stopped_reason = "Unpriced returned usage; further requests withheld."
            else:
                self.budget.spent += cost
                if cost > self.amount or self.budget.spent > self.budget.limit_usd:
                    self.budget.stopped_reason = (
                        "Returned usage exceeded its estimate; further requests withheld."
                    )
            self.completed = True

    def __exit__(self, exc_type, exc, tb):
        with self.budget.lock:
            if self.closed:
                return False
            self.closed = True
            self.budget.reserved = max(0.0, self.budget.reserved - self.amount)
            if not self.completed:
                self.budget.stopped_reason = (
                    "Provider request did not return priced usage; further requests withheld."
                )
                self.budget.calls.append(
                    {
                        "purpose": self.purpose,
                        "model": self.model,
                        "estimated_usd": None,
                        "error_type": exc_type.__name__ if exc_type else "MissingUsage",
                    }
                )
        return False


def current_budget():
    return _ACTIVE.get()


@contextmanager
def model_budget(limit_usd: float):
    existing = current_budget()
    if existing is not None:
        if limit_usd < existing.limit_usd:
            raise ValueError("A nested budget cannot replace the active experiment limit.")
        yield existing
        return
    budget = ModelBudget(limit_usd)
    token = _ACTIVE.set(budget)
    try:
        yield budget
    finally:
        _ACTIVE.reset(token)
