"""Tests for UnifiedLLMClient."""

from __future__ import annotations

import pytest

from llm_integration_starter.client import LLMResponse, UnifiedLLMClient


class TestUnifiedLLMClient:
    """Tests for the unified client."""

    def test_client_initialization(self):
        """Test client can be initialized with default provider."""
        client = UnifiedLLMClient()
        assert client.provider_name == "mock"

    def test_client_with_custom_provider(self):
        """Test client can be initialized with specific provider."""
        client = UnifiedLLMClient(provider="mock")
        assert client.provider_name == "mock"

    def test_client_with_unknown_provider(self):
        """Test client raises error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            UnifiedLLMClient(provider="nonexistent")

    def test_complete_returns_response(self, mock_client, sample_messages):
        """Test complete() returns LLMResponse."""
        response = mock_client.complete(sample_messages)
        assert isinstance(response, LLMResponse)
        assert response.text == "Mock response"
        assert response.provider == "mock"

    def test_complete_with_custom_response(self, sample_messages):
        """Test complete() with custom mock response."""
        client = UnifiedLLMClient(provider="mock", default_response="Custom answer")
        response = client.complete(sample_messages)
        assert response.text == "Custom answer"

    def test_complete_includes_metadata(self, mock_client, sample_messages):
        """Test response includes all metadata fields."""
        response = mock_client.complete(sample_messages)
        assert response.input_tokens > 0
        assert response.output_tokens > 0
        assert response.cost >= 0
        assert response.latency_ms > 0
        assert response.model

    def test_list_providers(self, mock_client):
        """Test listing available providers."""
        providers = mock_client.list_providers()
        assert "mock" in providers
        assert len(providers) >= 1

    def test_provider_property(self, mock_client):
        """Test access to underlying provider instance."""
        from llm_integration_starter.providers.base import BaseProvider

        assert isinstance(mock_client.provider, BaseProvider)

    def test_complete_with_kwargs(self, mock_client, sample_messages):
        """Test complete() accepts keyword arguments."""
        response = mock_client.complete(sample_messages, temperature=0.5, max_tokens=100)
        assert isinstance(response, LLMResponse)

    def test_multiple_messages(self, mock_client):
        """Test complete() with multiple messages."""
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
        ]
        response = mock_client.complete(messages)
        assert response.input_tokens > 0

    def test_complete_with_tools_not_implemented(self, mock_client, sample_messages):
        """Test complete_with_tools() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            mock_client.complete_with_tools(sample_messages, tools=[])

    def test_stream_not_implemented(self, mock_client, sample_messages):
        """Test stream() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            list(mock_client.stream(sample_messages))
