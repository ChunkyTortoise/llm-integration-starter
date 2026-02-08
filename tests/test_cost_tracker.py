"""Tests for CostTracker."""

from __future__ import annotations

from llm_starter.cost_tracker import CostRecord, CostTracker


class TestCostTracker:
    """Tests for CostTracker."""

    def test_record_cost(self) -> None:
        tracker = CostTracker()
        record = tracker.record("mock-gpt-4", 100, 50)
        assert isinstance(record, CostRecord)
        assert record.model == "mock-gpt-4"
        assert record.cost_usd > 0

    def test_summary_totals(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 100, 50)
        tracker.record("mock-gpt-4", 200, 100)
        summary = tracker.get_summary()
        assert summary.total_requests == 2
        assert summary.total_prompt_tokens == 300
        assert summary.total_completion_tokens == 150

    def test_cost_by_model(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 100, 50)
        tracker.record("mock-gpt-3.5", 100, 50)
        summary = tracker.get_summary()
        assert "mock-gpt-4" in summary.cost_by_model
        assert "mock-gpt-3.5" in summary.cost_by_model
        # GPT-4 should cost more than GPT-3.5
        assert summary.cost_by_model["mock-gpt-4"] > summary.cost_by_model["mock-gpt-3.5"]

    def test_avg_cost_per_request(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 1000, 500)
        tracker.record("mock-gpt-4", 1000, 500)
        summary = tracker.get_summary()
        assert summary.avg_cost_per_request == summary.total_cost / 2

    def test_projections(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 100, 50)
        tracker.record("mock-gpt-4", 100, 50)
        summary = tracker.get_summary()
        assert summary.daily_projection >= 0
        assert summary.monthly_projection >= 0
        assert summary.monthly_projection >= summary.daily_projection

    def test_empty_summary(self) -> None:
        tracker = CostTracker()
        summary = tracker.get_summary()
        assert summary.total_cost == 0.0
        assert summary.total_requests == 0
        assert summary.cost_by_model == {}

    def test_reset(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 100, 50)
        tracker.reset()
        assert len(tracker.get_records()) == 0
        summary = tracker.get_summary()
        assert summary.total_requests == 0

    def test_custom_pricing(self) -> None:
        custom_pricing = {"custom-model": {"input": 0.1, "output": 0.2}}
        tracker = CostTracker(pricing=custom_pricing)
        record = tracker.record("custom-model", 1000, 1000)
        # 1000/1000 * 0.1 + 1000/1000 * 0.2 = 0.3
        assert abs(record.cost_usd - 0.3) < 0.001

    def test_unknown_model_uses_default(self) -> None:
        tracker = CostTracker()
        record = tracker.record("unknown-model", 1000, 1000)
        # Should use fallback pricing (0.01 input, 0.03 output)
        assert record.cost_usd > 0

    def test_get_records_returns_copy(self) -> None:
        tracker = CostTracker()
        tracker.record("mock-gpt-4", 100, 50)
        records = tracker.get_records()
        records.clear()
        assert len(tracker.get_records()) == 1
