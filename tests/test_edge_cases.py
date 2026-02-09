"""Edge-case tests for cache, fallback, retry, token counter, and mock provider.

Covers TTL boundaries, LRU ordering under access, eviction cascades,
fallback error propagation, circuit breaker state transitions after
half-open failure, provider-specific token counting, cost estimation
for all provider/model combos, and mock provider precision.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from llm_integration_starter.cache import LRUCache
from llm_integration_starter.client import LLMResponse, UnifiedLLMClient
from llm_integration_starter.fallback import FallbackChain, FallbackResult
from llm_integration_starter.providers.mock import MockProvider
from llm_integration_starter.retry import CircuitBreaker, RetryPolicy
from llm_integration_starter.token_counter import TokenCounter


# ---------------------------------------------------------------------------
# Cache edge cases
# ---------------------------------------------------------------------------


class TestCacheEdgeCases:
    """Edge-case tests for LRUCache."""

    def _make_response(self, text: str = "resp") -> LLMResponse:
        return LLMResponse(
            text=text, input_tokens=1, output_tokens=1,
            cost=0.0, latency_ms=1.0, provider="mock", model="m",
        )

    def test_lru_access_promotes_item_preventing_eviction(self):
        """Accessing an item moves it to end, so the *other* item is evicted."""
        cache = LRUCache(max_size=2)
        cache.put("a", self._make_response("A"))
        cache.put("b", self._make_response("B"))

        # Access 'a' to promote it; 'b' is now least-recently-used
        cache.get("a")

        # Insert 'c' -- should evict 'b', not 'a'
        cache.put("c", self._make_response("C"))

        assert cache.get("a") is not None, "a should survive (recently accessed)"
        assert cache.get("b") is None, "b should be evicted (LRU)"
        assert cache.get("c") is not None

    def test_multiple_evictions_cascade(self):
        """Filling well past max_size evicts multiple old entries."""
        cache = LRUCache(max_size=3)
        for i in range(10):
            cache.put(f"k{i}", self._make_response(f"v{i}"))

        assert cache.size == 3
        # Only the last 3 should survive
        for i in range(7):
            assert cache.get(f"k{i}") is None
        for i in range(7, 10):
            assert cache.get(f"k{i}") is not None

    def test_ttl_boundary_item_available_just_before_expiry(self):
        """An item should still be retrievable just before its TTL elapses."""
        cache = LRUCache(ttl_seconds=0.3)
        cache.put("k", self._make_response())

        time.sleep(0.1)  # well within TTL
        assert cache.get("k") is not None, "should still be valid before TTL"

    def test_expired_get_decreases_size(self):
        """Getting an expired key removes it, reducing cache size."""
        cache = LRUCache(ttl_seconds=0.05)
        cache.put("k", self._make_response())
        assert cache.size == 1

        time.sleep(0.1)
        cache.get("k")  # triggers removal
        assert cache.size == 0

    def test_make_key_varies_with_temperature(self):
        """Different temperatures produce different cache keys."""
        cache = LRUCache()
        msgs = [{"role": "user", "content": "hi"}]
        k1 = cache.make_key("mock", "m", msgs, temperature=0.0)
        k2 = cache.make_key("mock", "m", msgs, temperature=1.0)
        assert k1 != k2

    def test_make_key_varies_with_model(self):
        """Different model names produce different cache keys."""
        cache = LRUCache()
        msgs = [{"role": "user", "content": "hi"}]
        k1 = cache.make_key("mock", "model-a", msgs)
        k2 = cache.make_key("mock", "model-b", msgs)
        assert k1 != k2

    def test_make_key_varies_with_message_content(self):
        """Different message content produces different cache keys."""
        cache = LRUCache()
        k1 = cache.make_key("mock", "m", [{"role": "user", "content": "hello"}])
        k2 = cache.make_key("mock", "m", [{"role": "user", "content": "goodbye"}])
        assert k1 != k2

    def test_hit_rate_zero_with_no_operations(self):
        """hit_rate should be 0.0 when no gets have been performed (no division by zero)."""
        cache = LRUCache()
        assert cache.hit_rate == 0.0

    def test_stats_after_clear_are_zeroed(self):
        """After clear(), stats counters reset to zero."""
        cache = LRUCache()
        cache.put("k", self._make_response())
        cache.get("k")  # hit
        cache.get("x")  # miss
        cache.clear()

        stats = cache.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        assert stats["hit_rate"] == 0.0

    def test_update_existing_key_does_not_evict(self):
        """Updating an existing key in a full cache should not trigger eviction."""
        cache = LRUCache(max_size=2)
        r1 = self._make_response("v1")
        r2 = self._make_response("v2")

        cache.put("a", r1)
        cache.put("b", r1)
        # Cache is full (2/2). Update 'a' -- should NOT evict 'b'.
        cache.put("a", r2)

        assert cache.size == 2
        assert cache.get("a").text == "v2"
        assert cache.get("b") is not None


# ---------------------------------------------------------------------------
# Fallback edge cases
# ---------------------------------------------------------------------------


class TestFallbackEdgeCases:
    """Edge-case tests for FallbackChain."""

    def test_fallback_to_second_provider_on_first_failure(self):
        """When the first provider fails, the chain should succeed with the second."""
        chain = FallbackChain(
            providers=["bad_provider", "mock"],
        )
        messages = [{"role": "user", "content": "hi"}]

        # "bad_provider" is unknown to UnifiedLLMClient, so it raises ValueError;
        # "mock" should succeed
        result = chain.execute(messages)
        assert result.successful_provider == "mock"
        assert result.attempts == 2
        assert len(result.errors) == 1
        assert "bad_provider" in result.errors[0]

    def test_all_providers_fail_raises_last_exception(self):
        """When every provider fails, the last exception is raised."""
        chain = FallbackChain(providers=["nonexistent_1", "nonexistent_2"])
        messages = [{"role": "user", "content": "hi"}]

        with pytest.raises(ValueError, match="Unknown provider"):
            chain.execute(messages)

    def test_add_new_provider_extends_chain(self):
        """add_provider with a genuinely new name extends the list."""
        chain = FallbackChain(providers=["mock"])
        chain.add_provider("openai")
        assert chain.get_providers() == ["mock", "openai"]

    def test_execute_returns_errors_from_failed_attempts(self):
        """The FallbackResult.errors list contains formatted error strings."""
        chain = FallbackChain(providers=["no_such", "mock"])
        messages = [{"role": "user", "content": "test"}]

        result = chain.execute(messages)
        assert len(result.errors) == 1
        assert "ValueError" in result.errors[0]

    def test_provider_kwargs_passed_to_mock(self):
        """provider_kwargs for 'mock' are forwarded to MockProvider."""
        chain = FallbackChain(
            providers=["mock"],
            provider_kwargs={"mock": {"default_response": "custom answer"}},
        )
        messages = [{"role": "user", "content": "hi"}]
        result = chain.execute(messages)
        assert result.response.text == "custom answer"

    def test_get_providers_returns_defensive_copy(self):
        """Mutating the returned list should not affect internal state."""
        chain = FallbackChain(providers=["mock"])
        providers = chain.get_providers()
        providers.clear()
        assert chain.get_providers() == ["mock"]


# ---------------------------------------------------------------------------
# Retry / CircuitBreaker edge cases
# ---------------------------------------------------------------------------


class TestRetryPolicyEdgeCases:
    """Edge-case tests for RetryPolicy."""

    def test_backoff_attempt_zero_equals_base(self):
        """At attempt 0 with no jitter, backoff should equal backoff_base."""
        policy = RetryPolicy(backoff_base=0.5, backoff_multiplier=3.0, jitter=False)
        assert policy.calculate_backoff(0) == 0.5

    def test_backoff_with_custom_multiplier(self):
        """Verify backoff grows by the configured multiplier (no jitter)."""
        policy = RetryPolicy(backoff_base=1.0, backoff_multiplier=3.0, jitter=False)
        assert policy.calculate_backoff(0) == 1.0
        assert policy.calculate_backoff(1) == 3.0
        assert policy.calculate_backoff(2) == 9.0

    def test_jitter_stays_within_bounds_over_many_samples(self):
        """Over many samples, jitter should remain within [0.5x, 1.5x] of base backoff."""
        policy = RetryPolicy(backoff_base=2.0, backoff_multiplier=2.0, jitter=True)
        base_at_1 = 2.0 * 2.0  # 4.0
        results = [policy.calculate_backoff(1) for _ in range(200)]
        assert all(base_at_1 * 0.5 <= r <= base_at_1 * 1.5 for r in results)
        # With 200 samples we expect *some* variance; not all identical
        assert len(set(results)) > 1

    def test_backoff_large_attempt_number(self):
        """Backoff should grow exponentially for large attempt numbers."""
        policy = RetryPolicy(backoff_base=1.0, backoff_multiplier=2.0, jitter=False)
        assert policy.calculate_backoff(10) == 1024.0


class TestCircuitBreakerEdgeCases:
    """Edge-case tests for CircuitBreaker."""

    def test_failure_count_continues_incrementing_past_threshold(self):
        """Failures beyond threshold still increment the counter."""
        breaker = CircuitBreaker(failure_threshold=2)
        for _ in range(5):
            breaker.record_failure()
        assert breaker.failure_count == 5
        assert breaker.state == "open"

    def test_half_open_failure_reopens_circuit(self):
        """A failure in half-open state should reopen the circuit."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        time.sleep(0.1)
        breaker.is_open()  # transition to half-open
        assert breaker.state == "half_open"

        # Failure in half-open should re-open
        breaker.record_failure()
        assert breaker._state.value == "open"

    def test_reset_clears_last_failure_time(self):
        """reset() should zero out _last_failure_time."""
        breaker = CircuitBreaker(failure_threshold=2)
        breaker.record_failure()
        assert breaker._last_failure_time > 0
        breaker.reset()
        assert breaker._last_failure_time == 0.0

    def test_multiple_successes_keep_circuit_closed(self):
        """Recording multiple successes does not change state from closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        for _ in range(10):
            breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

    def test_success_after_partial_failures_resets_count(self):
        """A success after some (but not threshold) failures resets count to 0."""
        breaker = CircuitBreaker(failure_threshold=5)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 3
        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "closed"


# ---------------------------------------------------------------------------
# TokenCounter edge cases
# ---------------------------------------------------------------------------


class TestTokenCounterEdgeCases:
    """Edge-case tests for TokenCounter."""

    def test_count_tokens_mock_uses_word_split(self):
        """Mock provider counts tokens by whitespace splitting."""
        assert TokenCounter.count_tokens("one two three", "mock") == 3

    def test_count_tokens_openai_uses_char_division(self):
        """Non-mock providers use chars_per_token (4) division."""
        text = "abcdefgh"  # 8 chars / 4 = 2
        assert TokenCounter.count_tokens(text, "openai") == 2

    def test_count_tokens_claude_uses_char_division(self):
        """Claude provider also uses char-based counting."""
        text = "abcdefghijkl"  # 12 chars / 4 = 3
        assert TokenCounter.count_tokens(text, "claude") == 3

    def test_count_tokens_empty_string_mock(self):
        """Empty string with mock provider should return 0 (split produces [''])."""
        # "".split() returns [] so len is 0
        assert TokenCounter.count_tokens("", "mock") == 0

    def test_count_tokens_empty_string_openai(self):
        """Empty string with openai provider returns 0 (0 // 4 = 0)."""
        assert TokenCounter.count_tokens("", "openai") == 0

    def test_count_message_tokens_openai_adds_4_per_message(self):
        """OpenAI provider adds 4 overhead tokens per message plus 3 base."""
        messages = [{"role": "user", "content": "abcdefgh"}]  # 8 / 4 = 2 + 4 overhead
        total = TokenCounter.count_message_tokens(messages, "openai")
        # 2 (content) + 4 (openai overhead) + 3 (base) = 9
        assert total == 9

    def test_count_message_tokens_claude_adds_3_per_message(self):
        """Claude provider adds 3 overhead tokens per message plus 3 base."""
        messages = [{"role": "user", "content": "abcdefgh"}]  # 8 / 4 = 2 + 3 overhead
        total = TokenCounter.count_message_tokens(messages, "claude")
        # 2 (content) + 3 (claude overhead) + 3 (base) = 8
        assert total == 8

    def test_count_message_tokens_mock_adds_2_per_message(self):
        """Mock/other provider adds 2 overhead tokens per message plus 3 base."""
        messages = [{"role": "user", "content": "one two"}]  # 2 words + 2 overhead
        total = TokenCounter.count_message_tokens(messages, "mock")
        # 2 (words) + 2 (mock overhead) + 3 (base) = 7
        assert total == 7

    def test_count_message_tokens_empty_list(self):
        """Empty message list should return only the base 3 tokens."""
        assert TokenCounter.count_message_tokens([], "mock") == 3

    def test_count_message_tokens_missing_content_key(self):
        """Messages without a 'content' key should default to empty string."""
        messages = [{"role": "user"}]
        # content="" -> 0 tokens (mock: "".split() = []) + 2 overhead + 3 base = 5
        total = TokenCounter.count_message_tokens(messages, "mock")
        assert total == 5

    def test_estimate_cost_known_model(self):
        """estimate_cost returns correct cost for a known provider/model."""
        # claude-3-haiku: input=$0.25/M, output=$1.25/M
        cost = TokenCounter.estimate_cost(1_000_000, 1_000_000, "claude", "claude-3-haiku")
        assert cost == pytest.approx(0.25 + 1.25)

    def test_estimate_cost_unknown_provider_returns_zero(self):
        """Unknown provider defaults to (0.0, 0.0) pricing -> $0."""
        cost = TokenCounter.estimate_cost(1000, 1000, "unknown_provider", "unknown_model")
        assert cost == 0.0

    def test_estimate_cost_unknown_model_returns_zero(self):
        """Known provider but unknown model defaults to (0.0, 0.0) -> $0."""
        cost = TokenCounter.estimate_cost(1000, 1000, "openai", "nonexistent-model")
        assert cost == 0.0

    def test_estimate_cost_zero_tokens(self):
        """Zero input and output tokens should produce zero cost."""
        cost = TokenCounter.estimate_cost(0, 0, "openai", "gpt-4-turbo")
        assert cost == 0.0

    def test_count_message_tokens_multiple_messages(self):
        """Multiple messages accumulate per-message overhead."""
        messages = [
            {"role": "user", "content": "abcd"},      # 1 token (4/4)
            {"role": "assistant", "content": "efgh"},  # 1 token (4/4)
        ]
        total = TokenCounter.count_message_tokens(messages, "openai")
        # (1+4) + (1+4) + 3 = 13
        assert total == 13


# ---------------------------------------------------------------------------
# MockProvider edge cases
# ---------------------------------------------------------------------------


class TestMockProviderEdgeCases:
    """Edge-case tests for MockProvider."""

    def test_zero_latency_completes_quickly(self):
        """MockProvider with latency_ms=0 should complete with near-zero latency."""
        provider = MockProvider(latency_ms=0)
        messages = [{"role": "user", "content": "hi"}]
        response = provider.complete(messages)
        assert response.latency_ms < 50  # generous bound; should be ~0

    def test_cost_matches_manual_calculation(self):
        """Verify the cost returned matches manual formula."""
        provider = MockProvider(
            default_response="one two three",
            input_cost_per_1k=0.01,
            output_cost_per_1k=0.02,
        )
        messages = [{"role": "user", "content": "hello world"}]
        response = provider.complete(messages)

        # input: "hello world" -> 2 words; output: "one two three" -> 3 words
        expected_cost = (2 / 1000.0) * 0.01 + (3 / 1000.0) * 0.02
        assert response.cost == pytest.approx(expected_cost)

    def test_messages_without_content_key(self):
        """Messages missing 'content' should be treated as empty string."""
        provider = MockProvider()
        messages = [{"role": "system"}]
        response = provider.complete(messages)
        assert response.input_tokens == 0

    def test_response_metadata_fields(self):
        """Verify all metadata fields are populated."""
        provider = MockProvider(default_response="test", latency_ms=10)
        messages = [{"role": "user", "content": "a b c"}]
        response = provider.complete(messages)

        assert response.provider == "mock"
        assert response.model == "mock-model"
        assert response.input_tokens == 3  # "a b c" -> 3 words
        assert response.output_tokens == 1  # "test" -> 1 word
        assert response.latency_ms >= 10
