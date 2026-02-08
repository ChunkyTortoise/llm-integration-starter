"""Tests for provider implementations."""

from __future__ import annotations

import pytest

from llm_integration_starter.client import LLMResponse
from llm_integration_starter.providers.base import BaseProvider
from llm_integration_starter.providers.mock import MockProvider


class TestBaseProvider:
    """Tests for BaseProvider abstract class."""

    def test_base_provider_is_abstract(self):
        """Test that BaseProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseProvider()  # type: ignore

    def test_base_provider_defines_interface(self):
        """Test that BaseProvider defines required methods."""
        assert hasattr(BaseProvider, "complete")
        assert hasattr(BaseProvider, "count_tokens")
        assert hasattr(BaseProvider, "estimate_cost")


class TestMockProvider:
    """Tests for MockProvider."""

    def test_mock_provider_initialization(self):
        """Test mock provider can be initialized."""
        provider = MockProvider()
        assert provider.default_response == "Mock response"

    def test_mock_provider_with_custom_response(self):
        """Test mock provider with custom response."""
        provider = MockProvider(default_response="Custom response")
        assert provider.default_response == "Custom response"

    def test_mock_provider_complete(self, mock_provider):
        """Test mock provider complete() method."""
        messages = [{"role": "user", "content": "Hello"}]
        response = mock_provider.complete(messages)

        assert isinstance(response, LLMResponse)
        assert response.text == "Test response"
        assert response.provider == "mock"
        assert response.model == "mock-model"

    def test_mock_provider_counts_tokens(self, mock_provider):
        """Test mock provider counts tokens correctly."""
        token_count = mock_provider.count_tokens("Hello world test")
        assert token_count == 3  # Simple whitespace split

    def test_mock_provider_estimates_cost(self, mock_provider):
        """Test mock provider estimates cost."""
        cost = mock_provider.estimate_cost(input_tokens=100, output_tokens=50)
        assert cost > 0
        assert isinstance(cost, float)

    def test_mock_provider_latency_simulation(self):
        """Test mock provider simulates latency."""
        provider = MockProvider(latency_ms=50)
        messages = [{"role": "user", "content": "Test"}]
        response = provider.complete(messages)

        # Latency should be approximately the configured value
        assert response.latency_ms >= 50

    def test_mock_provider_custom_pricing(self):
        """Test mock provider with custom pricing."""
        provider = MockProvider(
            input_cost_per_1k=0.01,
            output_cost_per_1k=0.02,
        )
        cost = provider.estimate_cost(input_tokens=1000, output_tokens=1000)
        assert cost == 0.03  # 0.01 + 0.02

    def test_mock_provider_inherits_base_provider(self):
        """Test mock provider inherits from BaseProvider."""
        provider = MockProvider()
        assert isinstance(provider, BaseProvider)

    def test_mock_provider_empty_message(self, mock_provider):
        """Test mock provider handles empty messages."""
        messages = [{"role": "user", "content": ""}]
        response = mock_provider.complete(messages)
        assert isinstance(response, LLMResponse)

    def test_mock_provider_multiple_messages(self, mock_provider):
        """Test mock provider handles multiple messages."""
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second"},
        ]
        response = mock_provider.complete(messages)
        assert response.input_tokens > 0

    def test_count_tokens_empty_string(self, mock_provider):
        """Test counting tokens in empty string."""
        count = mock_provider.count_tokens("")
        assert count == 0
