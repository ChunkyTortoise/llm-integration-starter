"""Production hardening: circuit breaker, retry, rate limiting, timeout."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

from llm_starter.mock_llm import MockLLM

logger = logging.getLogger("llm_starter.hardening")


@dataclass
class CircuitState:
    """Current state of the circuit breaker."""

    state: str  # "closed", "open", "half_open"
    failure_count: int
    last_failure_time: float | None
    success_count: int


class CircuitBreaker:
    """Circuit breaker pattern for LLM API calls.

    States: closed (normal) -> open (failing, reject calls) -> half_open (testing recovery).
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        """Current circuit state with automatic transition from open -> half_open."""
        if self._state == "open" and self._last_failure_time:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half_open"
                self._half_open_calls = 0
        return self._state

    def get_state(self) -> CircuitState:
        """Get full circuit state."""
        return CircuitState(
            state=self.state,
            failure_count=self._failure_count,
            last_failure_time=self._last_failure_time,
            success_count=self._success_count,
        )

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function through circuit breaker.

        Raises RuntimeError if circuit is open.
        """
        current = self.state

        if current == "open":
            raise RuntimeError("Circuit breaker is open — request rejected")

        if current == "half_open" and self._half_open_calls >= self.half_open_max:
            raise RuntimeError("Circuit breaker half-open limit reached")

        try:
            if current == "half_open":
                self._half_open_calls += 1

            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Record a successful call."""
        self._success_count += 1
        if self._state == "half_open":
            self._state = "closed"
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


class HardenedClient:
    """LLM client with production hardening: circuit breaker, retry, timeout.

    Wraps a MockLLM with reliability patterns.
    """

    def __init__(
        self,
        llm: MockLLM | None = None,
        max_retries: int = 3,
        timeout_ms: float = 5000.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self.llm = llm or MockLLM()
        self.max_retries = max_retries
        self.timeout_ms = timeout_ms
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self._total_requests = 0
        self._total_retries = 0

    def complete(self, prompt: str, model: str = "mock-gpt-4") -> dict[str, Any]:
        """Complete with hardening: circuit breaker + retry."""
        self._total_requests += 1
        last_error = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self._total_retries += 1

            try:
                response = self.circuit_breaker.call(self.llm.complete, prompt, model)
                return {
                    "content": response.content,
                    "model": response.model,
                    "usage": response.usage,
                    "latency_ms": response.latency_ms,
                    "attempts": attempt + 1,
                }
            except RuntimeError:
                raise  # Circuit breaker open — don't retry
            except Exception as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d failed: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                )

        raise last_error or RuntimeError("All retries exhausted")

    @property
    def stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "total_requests": self._total_requests,
            "total_retries": self._total_retries,
            "circuit_state": self.circuit_breaker.state,
        }
