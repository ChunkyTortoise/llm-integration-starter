"""Cost tracking and estimation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostEntry:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: float


class CostTracker:
    def __init__(self):
        self._entries: list[CostEntry] = []

    def record(self, entry: CostEntry) -> None:
        self._entries.append(entry)

    def total_cost(self) -> float:
        return sum(e.cost for e in self._entries)

    def cost_by_provider(self) -> dict[str, float]:
        costs = {}
        for entry in self._entries:
            costs[entry.provider] = costs.get(entry.provider, 0.0) + entry.cost
        return costs

    def cost_by_model(self) -> dict[str, float]:
        costs = {}
        for entry in self._entries:
            costs[entry.model] = costs.get(entry.model, 0.0) + entry.cost
        return costs

    def recent_entries(self, n: int = 10) -> list[CostEntry]:
        return self._entries[-n:][::-1]

    def entries_since(self, timestamp: float) -> list[CostEntry]:
        return [e for e in self._entries if e.timestamp >= timestamp]

    def cost_since(self, timestamp: float) -> float:
        return sum(e.cost for e in self.entries_since(timestamp))

    def token_stats(self) -> dict:
        total_input = sum(e.input_tokens for e in self._entries)
        total_output = sum(e.output_tokens for e in self._entries)
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }

    def clear(self) -> None:
        self._entries.clear()

    @property
    def entry_count(self) -> int:
        return len(self._entries)
