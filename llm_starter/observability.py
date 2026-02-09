"""LLM observability collector for request tracing and health monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass

# Approximate token costs per provider/model (USD per 1K tokens)
_TOKEN_COSTS: dict[str, float] = {
    "openai/gpt-4": 0.03,
    "openai/gpt-3.5-turbo": 0.002,
    "anthropic/claude-3": 0.015,
    "default": 0.01,
}


@dataclass
class RequestTrace:
    """A single LLM request trace."""

    trace_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    status: str  # "success", "error", "timeout"
    error: str | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class HealthStatus:
    """System health status summary."""

    healthy: bool
    uptime_seconds: float
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    p95_latency_ms: float


class ObservabilityCollector:
    """Collects and analyzes LLM request traces."""

    def __init__(self) -> None:
        self._traces: list[RequestTrace] = []
        self._start_time: float = time.time()

    def record(self, trace: RequestTrace) -> None:
        """Record a request trace."""
        if trace.timestamp == 0.0:
            trace.timestamp = time.time()
        self._traces.append(trace)

    def get_traces(self, limit: int = 100, provider: str | None = None) -> list[RequestTrace]:
        """Retrieve traces, optionally filtered by provider."""
        traces = self._traces
        if provider is not None:
            traces = [t for t in traces if t.provider == provider]
        return traces[-limit:]

    def health_check(self) -> HealthStatus:
        """Compute current health status."""
        total = len(self._traces)
        uptime = time.time() - self._start_time

        if total == 0:
            return HealthStatus(
                healthy=True,
                uptime_seconds=uptime,
                total_requests=0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
            )

        errors = sum(1 for t in self._traces if t.status != "success")
        err_rate = errors / total
        latencies = [t.latency_ms for t in self._traces]
        avg_lat = sum(latencies) / len(latencies)
        p95_lat = self.latency_percentile(95.0)

        return HealthStatus(
            healthy=err_rate < 0.5,
            uptime_seconds=uptime,
            total_requests=total,
            error_rate=round(err_rate, 4),
            avg_latency_ms=round(avg_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
        )

    def error_rate(self, window_seconds: float = 300) -> float:
        """Compute error rate within a time window."""
        cutoff = time.time() - window_seconds
        recent = [t for t in self._traces if t.timestamp >= cutoff]
        if not recent:
            return 0.0
        errors = sum(1 for t in recent if t.status != "success")
        return round(errors / len(recent), 4)

    def latency_percentile(self, percentile: float = 95.0) -> float:
        """Compute latency at a given percentile."""
        if not self._traces:
            return 0.0
        latencies = sorted(t.latency_ms for t in self._traces)
        idx = int(len(latencies) * percentile / 100)
        idx = min(idx, len(latencies) - 1)
        return latencies[idx]

    def cost_summary(self) -> dict[str, float]:
        """Compute estimated costs by provider."""
        costs: dict[str, float] = {}
        for t in self._traces:
            key = f"{t.provider}/{t.model}"
            rate = _TOKEN_COSTS.get(key, _TOKEN_COSTS["default"])
            cost = (t.input_tokens + t.output_tokens) / 1000 * rate
            costs[t.provider] = costs.get(t.provider, 0.0) + cost
        # Round values
        return {k: round(v, 6) for k, v in costs.items()}

    def clear(self) -> None:
        """Clear all recorded traces."""
        self._traces.clear()
        self._start_time = time.time()
