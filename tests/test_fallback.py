"""Tests for fallback chain."""

from __future__ import annotations

import pytest

from llm_integration_starter.fallback import FallbackChain, FallbackResult


class TestFallbackChain:
    """Tests for FallbackChain."""

    def test_fallback_chain_initialization(self):
        """Test creating a fallback chain."""
        chain = FallbackChain(providers=["mock"])
        assert chain.providers == ["mock"]

    def test_fallback_chain_empty_providers_raises_error(self):
        """Test creating chain with no providers raises error."""
        with pytest.raises(ValueError, match="at least one provider"):
            FallbackChain(providers=[])

    def test_fallback_chain_execute_success(self):
        """Test successful execution with first provider."""
        chain = FallbackChain(providers=["mock"])
        messages = [{"role": "user", "content": "Hello"}]

        result = chain.execute(messages)

        assert isinstance(result, FallbackResult)
        assert result.successful_provider == "mock"
        assert result.attempts == 1
        assert len(result.errors) == 0

    def test_fallback_chain_get_providers(self):
        """Test getting provider list."""
        chain = FallbackChain(providers=["mock"])
        providers = chain.get_providers()
        assert providers == ["mock"]
        # Should return a copy
        providers.append("test")
        assert chain.providers == ["mock"]

    def test_fallback_chain_add_provider(self):
        """Test adding a provider."""
        chain = FallbackChain(providers=["mock"])
        chain.add_provider("mock")
        assert "mock" in chain.providers

    def test_fallback_chain_add_duplicate_provider(self):
        """Test adding duplicate provider is idempotent."""
        chain = FallbackChain(providers=["mock"])
        original_length = len(chain.providers)
        chain.add_provider("mock")
        # Should not add duplicate
        assert len(chain.providers) == original_length

    def test_fallback_chain_remove_provider(self):
        """Test removing a provider."""
        chain = FallbackChain(providers=["mock", "mock"])
        chain.remove_provider("mock")
        assert len(chain.providers) == 1

    def test_fallback_chain_remove_nonexistent_provider(self):
        """Test removing nonexistent provider raises error."""
        chain = FallbackChain(providers=["mock"])
        with pytest.raises(ValueError, match="not in chain"):
            chain.remove_provider("nonexistent")

    def test_fallback_chain_remove_last_provider(self):
        """Test removing last provider raises error."""
        chain = FallbackChain(providers=["mock"])
        with pytest.raises(ValueError, match="last provider"):
            chain.remove_provider("mock")

    def test_fallback_result_creation(self, sample_response):
        """Test creating a FallbackResult."""
        result = FallbackResult(
            response=sample_response,
            successful_provider="mock",
            attempts=1,
            errors=[],
        )
        assert result.successful_provider == "mock"
        assert result.attempts == 1
