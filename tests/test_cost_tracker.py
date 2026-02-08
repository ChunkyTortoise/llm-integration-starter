"""Tests for cost tracking."""

from __future__ import annotations

import time

from llm_integration_starter.cost_tracker import CostEntry, CostTracker


class TestCostEntry:
    """Tests for CostEntry dataclass."""

    def test_cost_entry_creation(self):
        """Test creating a cost entry."""
        entry = CostEntry(
            provider="claude",
            model="claude-3-5-sonnet",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
            timestamp=time.time(),
        )
        assert entry.provider == "claude"
        assert entry.input_tokens == 100
        assert entry.cost == 0.005


class TestCostTracker:
    """Tests for CostTracker."""

    def test_cost_tracker_initialization(self):
        """Test creating a cost tracker."""
        tracker = CostTracker()
        assert tracker.entry_count == 0

    def test_cost_tracker_record_entry(self):
        """Test recording a cost entry."""
        tracker = CostTracker()
        entry = CostEntry(
            provider="mock",
            model="mock-model",
            input_tokens=10,
            output_tokens=5,
            cost=0.001,
            timestamp=time.time(),
        )

        tracker.record(entry)
        assert tracker.entry_count == 1

    def test_cost_tracker_total_cost(self):
        """Test calculating total cost."""
        tracker = CostTracker()

        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=time.time(),
            )
        )
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.002,
                timestamp=time.time(),
            )
        )

        assert tracker.total_cost() == 0.003

    def test_cost_tracker_cost_by_provider(self):
        """Test grouping costs by provider."""
        tracker = CostTracker()

        tracker.record(
            CostEntry(
                provider="claude",
                model="model1",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=time.time(),
            )
        )
        tracker.record(
            CostEntry(
                provider="openai",
                model="model2",
                input_tokens=10,
                output_tokens=5,
                cost=0.002,
                timestamp=time.time(),
            )
        )

        costs = tracker.cost_by_provider()
        assert costs["claude"] == 0.001
        assert costs["openai"] == 0.002

    def test_cost_tracker_cost_by_model(self):
        """Test grouping costs by model."""
        tracker = CostTracker()

        tracker.record(
            CostEntry(
                provider="mock",
                model="model-a",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=time.time(),
            )
        )
        tracker.record(
            CostEntry(
                provider="mock",
                model="model-b",
                input_tokens=10,
                output_tokens=5,
                cost=0.002,
                timestamp=time.time(),
            )
        )

        costs = tracker.cost_by_model()
        assert costs["model-a"] == 0.001
        assert costs["model-b"] == 0.002

    def test_cost_tracker_recent_entries(self):
        """Test getting recent entries."""
        tracker = CostTracker()

        for i in range(5):
            tracker.record(
                CostEntry(
                    provider="mock",
                    model="mock",
                    input_tokens=10,
                    output_tokens=5,
                    cost=0.001,
                    timestamp=time.time(),
                )
            )

        recent = tracker.recent_entries(n=3)
        assert len(recent) == 3

    def test_cost_tracker_entries_since(self):
        """Test getting entries since timestamp."""
        tracker = CostTracker()
        now = time.time()

        # Old entry
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=now - 100,
            )
        )

        # Recent entry
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.002,
                timestamp=now,
            )
        )

        recent = tracker.entries_since(now - 50)
        assert len(recent) == 1
        assert recent[0].cost == 0.002

    def test_cost_tracker_cost_since(self):
        """Test calculating cost since timestamp."""
        tracker = CostTracker()
        now = time.time()

        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=now - 100,
            )
        )
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.002,
                timestamp=now,
            )
        )

        cost = tracker.cost_since(now - 50)
        assert cost == 0.002

    def test_cost_tracker_token_stats(self):
        """Test token statistics."""
        tracker = CostTracker()

        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=100,
                output_tokens=50,
                cost=0.001,
                timestamp=time.time(),
            )
        )
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=200,
                output_tokens=100,
                cost=0.002,
                timestamp=time.time(),
            )
        )

        stats = tracker.token_stats()
        assert stats["input_tokens"] == 300
        assert stats["output_tokens"] == 150
        assert stats["total_tokens"] == 450

    def test_cost_tracker_clear(self):
        """Test clearing the tracker."""
        tracker = CostTracker()
        tracker.record(
            CostEntry(
                provider="mock",
                model="mock",
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                timestamp=time.time(),
            )
        )

        tracker.clear()
        assert tracker.entry_count == 0
        assert tracker.total_cost() == 0.0
