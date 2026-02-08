"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from llm_integration_starter.client import LLMResponse, UnifiedLLMClient
from llm_integration_starter.providers.mock import MockProvider


@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    return UnifiedLLMClient(provider="mock")


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
    ]


@pytest.fixture
def sample_response():
    """Sample LLMResponse for testing."""
    return LLMResponse(
        text="I'm doing well, thank you!",
        input_tokens=10,
        output_tokens=8,
        cost=0.0001,
        latency_ms=150.0,
        provider="mock",
        model="mock-model",
    )


@pytest.fixture
def mock_provider():
    """Create a mock provider instance."""
    return MockProvider(default_response="Test response")
