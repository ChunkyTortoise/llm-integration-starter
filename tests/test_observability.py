"""Tests for LLM observability collector."""

from __future__ import annotations

import time

from llm_starter.observability import (
    HealthStatus,
    ObservabilityCollector,
    RequestTrace,
)


def _make_trace(
    provider: str = "openai",
    model: str = "gpt-4",
    status: str = "success",
    latency: float = 100.0,
    input_tokens: int = 100,
    output_tokens: int = 50,
    **kwargs: object,
) -> RequestTrace:
    return RequestTrace(
        trace_id=f"t-{time.monotonic_ns()}",
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency,
        status=status,
        timestamp=time.time(),
        **kwargs,
    )


class TestObservabilityCollector:
    def test_record_and_retrieve(self) -> None:
        c = ObservabilityCollector()
        t = _make_trace()
        c.record(t)
        traces = c.get_traces()
        assert len(traces) == 1
        assert traces[0].trace_id == t.trace_id

    def test_get_traces_with_limit(self) -> None:
        c = ObservabilityCollector()
        for _ in range(10):
            c.record(_make_trace())
        traces = c.get_traces(limit=3)
        assert len(traces) == 3

    def test_get_traces_filter_provider(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace(provider="openai"))
        c.record(_make_trace(provider="anthropic"))
        c.record(_make_trace(provider="openai"))
        traces = c.get_traces(provider="anthropic")
        assert len(traces) == 1
        assert traces[0].provider == "anthropic"

    def test_health_check_empty(self) -> None:
        c = ObservabilityCollector()
        h = c.health_check()
        assert isinstance(h, HealthStatus)
        assert h.healthy is True
        assert h.total_requests == 0
        assert h.error_rate == 0.0

    def test_health_check_with_traces(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace(status="success", latency=100.0))
        c.record(_make_trace(status="success", latency=200.0))
        h = c.health_check()
        assert h.total_requests == 2
        assert h.avg_latency_ms == 150.0
        assert h.healthy is True

    def test_health_check_unhealthy(self) -> None:
        c = ObservabilityCollector()
        for _ in range(3):
            c.record(_make_trace(status="error"))
        c.record(_make_trace(status="success"))
        h = c.health_check()
        assert h.healthy is False
        assert h.error_rate == 0.75

    def test_error_rate_within_window(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace(status="error"))
        c.record(_make_trace(status="success"))
        rate = c.error_rate(window_seconds=300)
        assert rate == 0.5

    def test_error_rate_empty(self) -> None:
        c = ObservabilityCollector()
        assert c.error_rate() == 0.0

    def test_latency_percentile_p50(self) -> None:
        c = ObservabilityCollector()
        for lat in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            c.record(_make_trace(latency=float(lat)))
        p50 = c.latency_percentile(50.0)
        assert 40 <= p50 <= 60

    def test_latency_percentile_p95(self) -> None:
        c = ObservabilityCollector()
        for lat in range(1, 101):
            c.record(_make_trace(latency=float(lat)))
        p95 = c.latency_percentile(95.0)
        assert p95 >= 90

    def test_latency_percentile_empty(self) -> None:
        c = ObservabilityCollector()
        assert c.latency_percentile() == 0.0

    def test_cost_summary_single_provider(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace(provider="openai", model="gpt-4", input_tokens=1000, output_tokens=500))
        costs = c.cost_summary()
        assert "openai" in costs
        assert costs["openai"] > 0

    def test_cost_summary_multiple_providers(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace(provider="openai", model="gpt-4", input_tokens=1000, output_tokens=0))
        c.record(_make_trace(provider="anthropic", model="claude-3", input_tokens=1000, output_tokens=0))
        costs = c.cost_summary()
        assert "openai" in costs
        assert "anthropic" in costs

    def test_cost_summary_empty(self) -> None:
        c = ObservabilityCollector()
        assert c.cost_summary() == {}

    def test_clear(self) -> None:
        c = ObservabilityCollector()
        c.record(_make_trace())
        c.record(_make_trace())
        c.clear()
        assert c.get_traces() == []
        h = c.health_check()
        assert h.total_requests == 0

    def test_trace_default_timestamp(self) -> None:
        before = time.time()
        t = RequestTrace(
            trace_id="test",
            provider="openai",
            model="gpt-4",
            input_tokens=10,
            output_tokens=5,
            latency_ms=50.0,
            status="success",
        )
        after = time.time()
        assert before <= t.timestamp <= after

    def test_trace_error_field(self) -> None:
        t = _make_trace(status="error", error="timeout")
        assert t.error == "timeout"
        assert t.status == "error"

    def test_many_traces_performance(self) -> None:
        c = ObservabilityCollector()
        for i in range(1000):
            c.record(_make_trace(latency=float(i)))
        h = c.health_check()
        assert h.total_requests == 1000
        assert h.avg_latency_ms > 0

    def test_get_traces_returns_most_recent(self) -> None:
        c = ObservabilityCollector()
        for i in range(20):
            c.record(_make_trace(latency=float(i)))
        traces = c.get_traces(limit=5)
        assert len(traces) == 5
        # Should be the last 5
        assert traces[0].latency_ms == 15.0
