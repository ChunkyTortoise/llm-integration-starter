"""Cost tracking: per-request pricing, daily/monthly projections."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# Pricing per 1K tokens (mock prices)
DEFAULT_PRICING = {
    "mock-gpt-4": {"input": 0.03, "output": 0.06},
    "mock-gpt-3.5": {"input": 0.001, "output": 0.002},
    "mock-claude": {"input": 0.015, "output": 0.075},
}


@dataclass
class CostRecord:
    """A single cost record."""

    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class CostSummary:
    """Summary of costs over a period."""

    total_cost: float
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_cost_per_request: float
    cost_by_model: dict[str, float]
    daily_projection: float
    monthly_projection: float


class CostTracker:
    """Track and project LLM API costs."""

    def __init__(self, pricing: dict[str, dict[str, float]] | None = None):
        self.pricing = pricing or DEFAULT_PRICING
        self._records: list[CostRecord] = []

    def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> CostRecord:
        """Record a request and compute its cost."""
        prices = self.pricing.get(model, {"input": 0.01, "output": 0.03})
        cost = (prompt_tokens / 1000 * prices["input"]) + (completion_tokens / 1000 * prices["output"])

        record = CostRecord(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=round(cost, 6),
        )
        self._records.append(record)
        return record

    def get_summary(self) -> CostSummary:
        """Get cost summary with projections."""
        if not self._records:
            return CostSummary(
                total_cost=0.0,
                total_requests=0,
                total_prompt_tokens=0,
                total_completion_tokens=0,
                avg_cost_per_request=0.0,
                cost_by_model={},
                daily_projection=0.0,
                monthly_projection=0.0,
            )

        total_cost = sum(r.cost_usd for r in self._records)
        total_requests = len(self._records)
        total_prompt = sum(r.prompt_tokens for r in self._records)
        total_completion = sum(r.completion_tokens for r in self._records)

        cost_by_model: dict[str, float] = {}
        for r in self._records:
            cost_by_model[r.model] = cost_by_model.get(r.model, 0.0) + r.cost_usd

        # Time-based projections
        if len(self._records) >= 2:
            time_span = self._records[-1].timestamp - self._records[0].timestamp
            if time_span > 0:
                rate_per_second = total_cost / time_span
                daily_projection = rate_per_second * 86400
                monthly_projection = daily_projection * 30
            else:
                daily_projection = total_cost * 100  # rough estimate
                monthly_projection = daily_projection * 30
        else:
            daily_projection = total_cost * 100
            monthly_projection = daily_projection * 30

        return CostSummary(
            total_cost=round(total_cost, 6),
            total_requests=total_requests,
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            avg_cost_per_request=round(total_cost / total_requests, 6),
            cost_by_model={k: round(v, 6) for k, v in cost_by_model.items()},
            daily_projection=round(daily_projection, 4),
            monthly_projection=round(monthly_projection, 4),
        )

    def get_records(self) -> list[CostRecord]:
        """Get all cost records."""
        return self._records.copy()

    def reset(self) -> None:
        """Clear all records."""
        self._records.clear()
