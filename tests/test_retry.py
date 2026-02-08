"""Tests for retry logic and circuit breaker."""

from __future__ import annotations

import time

from llm_integration_starter.retry import CircuitBreaker, CircuitState, RetryPolicy


class TestRetryPolicy:
    """Tests for RetryPolicy."""

    def test_retry_policy_creation(self):
        """Test creating a retry policy."""
        policy = RetryPolicy(max_retries=3, backoff_base=1.0)
        assert policy.max_retries == 3
        assert policy.backoff_base == 1.0

    def test_retry_policy_defaults(self):
        """Test default retry policy values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.backoff_base == 1.0
        assert policy.backoff_multiplier == 2.0
        assert policy.jitter is True

    def test_calculate_backoff_exponential(self):
        """Test exponential backoff calculation."""
        policy = RetryPolicy(backoff_base=1.0, backoff_multiplier=2.0, jitter=False)

        assert policy.calculate_backoff(0) == 1.0  # 1.0 * 2^0
        assert policy.calculate_backoff(1) == 2.0  # 1.0 * 2^1
        assert policy.calculate_backoff(2) == 4.0  # 1.0 * 2^2

    def test_calculate_backoff_with_jitter(self):
        """Test backoff with jitter is randomized."""
        policy = RetryPolicy(backoff_base=1.0, jitter=True)

        backoff = policy.calculate_backoff(1)
        # With jitter, backoff should be between 1.0 (2.0 * 0.5) and 3.0 (2.0 * 1.5)
        assert 1.0 <= backoff <= 3.0


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_circuit_breaker_initialization(self):
        """Test creating a circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60.0

    def test_circuit_breaker_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker()
        assert breaker.state == "closed"
        assert not breaker.is_open()

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3)

        # Record failures
        breaker.record_failure()
        assert not breaker.is_open()

        breaker.record_failure()
        assert not breaker.is_open()

        breaker.record_failure()
        assert breaker.is_open()
        assert breaker.state == "open"

    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets failure count on success."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "closed"

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters half-open state after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should transition to half-open
        assert not breaker.is_open()  # Half-open allows requests
        assert breaker.state == "half_open"

    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        breaker = CircuitBreaker(failure_threshold=2)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.is_open()

        breaker.reset()
        assert not breaker.is_open()
        assert breaker.failure_count == 0

    def test_circuit_breaker_failure_count_property(self):
        """Test failure_count property."""
        breaker = CircuitBreaker()
        assert breaker.failure_count == 0

        breaker.record_failure()
        assert breaker.failure_count == 1

    def test_circuit_state_enum(self):
        """Test CircuitState enum values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_circuit_breaker_state_transitions(self):
        """Test state transitions through circuit breaker lifecycle."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Start closed
        assert breaker.state == "closed"

        # Transition to open
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        # Transition to half-open after timeout
        time.sleep(0.2)
        breaker.is_open()  # Trigger state check
        assert breaker.state == "half_open"

        # Success transitions back to closed
        breaker.record_success()
        assert breaker.state == "closed"
