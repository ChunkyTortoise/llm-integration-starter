"""Tests for CircuitBreaker and HardenedClient."""

from __future__ import annotations

import time

import pytest

from llm_starter.hardening import CircuitBreaker, HardenedClient
from llm_starter.mock_llm import MockLLM


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_closed(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == "closed"

    def test_success_stays_closed(self) -> None:
        cb = CircuitBreaker()
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == "closed"

    def test_failures_open_circuit(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(self._failing_fn)
        assert cb.state == "open"

    def test_open_rejects_calls(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(self._failing_fn)
        with pytest.raises(RuntimeError, match="open"):
            cb.call(lambda: "should not run")

    def test_recovery_to_half_open(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(self._failing_fn)
        assert cb.state == "open"
        time.sleep(0.15)
        assert cb.state == "half_open"

    def test_half_open_success_closes(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(self._failing_fn)
        time.sleep(0.15)
        assert cb.state == "half_open"
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == "closed"

    def test_reset(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(self._failing_fn)
        assert cb.state == "open"
        cb.reset()
        assert cb.state == "closed"

    @staticmethod
    def _failing_fn() -> None:
        raise ValueError("simulated failure")


class TestHardenedClient:
    """Tests for HardenedClient."""

    def test_successful_completion(self) -> None:
        llm = MockLLM(default_response="hardened response")
        client = HardenedClient(llm)
        result = client.complete("test")
        assert result["content"] == "hardened response"
        assert result["attempts"] == 1

    def test_retry_on_failure(self) -> None:
        """Test that retries work by tracking attempts."""
        llm = MockLLM()
        client = HardenedClient(llm, max_retries=2)
        # Normal call should succeed on first try
        result = client.complete("test")
        assert result["attempts"] == 1

    def test_circuit_breaker_integration(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        llm = MockLLM()
        client = HardenedClient(llm, circuit_breaker=cb)
        result = client.complete("test")
        assert cb.state == "closed"
        assert result["content"] is not None

    def test_stats_tracking(self) -> None:
        client = HardenedClient()
        client.complete("test1")
        client.complete("test2")
        stats = client.stats
        assert stats["total_requests"] == 2
        assert stats["circuit_state"] == "closed"

    def test_open_circuit_raises(self) -> None:
        cb = CircuitBreaker(failure_threshold=1)
        # Trip the circuit
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        llm = MockLLM()
        client = HardenedClient(llm, circuit_breaker=cb)
        with pytest.raises(RuntimeError, match="open"):
            client.complete("should fail")
