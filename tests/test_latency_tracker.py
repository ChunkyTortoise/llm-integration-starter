"""Tests for LatencyTracker."""

from __future__ import annotations

from llm_starter.latency_tracker import LatencyTracker


class TestLatencyTracker:
    """Tests for LatencyTracker."""

    def test_record_latency(self) -> None:
        tracker = LatencyTracker()
        tracker.record(10.0)
        assert tracker.count == 1

    def test_percentiles(self) -> None:
        tracker = LatencyTracker()
        for i in range(100):
            tracker.record(float(i + 1))
        stats = tracker.get_stats()
        assert stats.p50 > 0
        assert stats.p95 > stats.p50
        assert stats.p99 >= stats.p95

    def test_p50_median(self) -> None:
        tracker = LatencyTracker()
        for v in [10, 20, 30, 40, 50]:
            tracker.record(float(v))
        stats = tracker.get_stats()
        assert stats.p50 == 30.0

    def test_p99_high(self) -> None:
        tracker = LatencyTracker()
        # 99 fast + 1 slow
        for _ in range(99):
            tracker.record(10.0)
        tracker.record(500.0)
        stats = tracker.get_stats()
        assert stats.p99 > 10.0

    def test_mean_calculation(self) -> None:
        tracker = LatencyTracker()
        tracker.record(10.0)
        tracker.record(20.0)
        tracker.record(30.0)
        stats = tracker.get_stats()
        assert stats.mean == 20.0

    def test_min_max(self) -> None:
        tracker = LatencyTracker()
        tracker.record(5.0)
        tracker.record(100.0)
        tracker.record(50.0)
        stats = tracker.get_stats()
        assert stats.min == 5.0
        assert stats.max == 100.0

    def test_empty_stats(self) -> None:
        tracker = LatencyTracker()
        stats = tracker.get_stats()
        assert stats.count == 0
        assert stats.p50 == 0.0
        assert stats.mean == 0.0

    def test_window_cleanup(self) -> None:
        tracker = LatencyTracker(window_seconds=0.1)
        tracker.record(10.0)
        import time

        time.sleep(0.15)
        tracker._cleanup()
        assert tracker.count == 0

    def test_reset(self) -> None:
        tracker = LatencyTracker()
        tracker.record(10.0)
        tracker.record(20.0)
        tracker.reset()
        assert tracker.count == 0

    def test_count_property(self) -> None:
        tracker = LatencyTracker()
        assert tracker.count == 0
        tracker.record(1.0)
        tracker.record(2.0)
        tracker.record(3.0)
        assert tracker.count == 3
