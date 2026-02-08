"""Latency tracking: P50/P95/P99 measurement with rolling window."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class LatencyStats:
    """Latency statistics."""

    p50: float
    p95: float
    p99: float
    mean: float
    min: float
    max: float
    count: int
    window_seconds: float


class LatencyTracker:
    """Track and measure LLM call latency with rolling window.

    Computes P50, P95, P99 percentiles over a configurable time window.
    """

    def __init__(self, window_seconds: float = 300.0):
        self.window_seconds = window_seconds
        self._records: list[tuple[float, float]] = []  # (timestamp, latency_ms)

    def record(self, latency_ms: float) -> None:
        """Record a latency measurement."""
        self._records.append((time.time(), latency_ms))
        self._cleanup()

    def _cleanup(self) -> None:
        """Remove records outside the window."""
        cutoff = time.time() - self.window_seconds
        self._records = [(t, lat) for t, lat in self._records if t >= cutoff]

    def get_stats(self) -> LatencyStats:
        """Get current latency statistics."""
        self._cleanup()

        if not self._records:
            return LatencyStats(
                p50=0.0,
                p95=0.0,
                p99=0.0,
                mean=0.0,
                min=0.0,
                max=0.0,
                count=0,
                window_seconds=self.window_seconds,
            )

        latencies = sorted(lat for _, lat in self._records)
        n = len(latencies)

        return LatencyStats(
            p50=self._percentile(latencies, 50),
            p95=self._percentile(latencies, 95),
            p99=self._percentile(latencies, 99),
            mean=round(sum(latencies) / n, 2),
            min=round(min(latencies), 2),
            max=round(max(latencies), 2),
            count=n,
            window_seconds=self.window_seconds,
        )

    @staticmethod
    def _percentile(sorted_data: list[float], pct: float) -> float:
        """Calculate percentile using linear interpolation."""
        n = len(sorted_data)
        if n == 0:
            return 0.0
        if n == 1:
            return round(sorted_data[0], 2)

        k = (pct / 100) * (n - 1)
        f = math.floor(k)
        c = min(math.ceil(k), n - 1)

        if f == c:
            return round(sorted_data[int(k)], 2)
        return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]), 2)

    @property
    def count(self) -> int:
        """Number of records in window."""
        self._cleanup()
        return len(self._records)

    def reset(self) -> None:
        """Clear all records."""
        self._records.clear()
