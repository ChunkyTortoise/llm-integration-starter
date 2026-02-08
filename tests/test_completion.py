"""Tests for CompletionClient and endpoint factory."""

from __future__ import annotations

import pytest

from llm_starter.completion import CompletionClient, CompletionResult
from llm_starter.mock_llm import MockLLM


class TestCompletionClient:
    """Tests for CompletionClient."""

    def test_basic_completion(self) -> None:
        llm = MockLLM(default_response="Hello!")
        client = CompletionClient(llm)
        result = client.complete("hi")
        assert result.content == "Hello!"

    def test_with_system_prompt(self) -> None:
        llm = MockLLM()
        client = CompletionClient(llm)
        client.complete("test", system="You are helpful.")
        log = llm.get_call_log()
        assert "You are helpful." in log[0]["prompt"]

    def test_with_context(self) -> None:
        llm = MockLLM()
        client = CompletionClient(llm)
        client.complete_with_context("What color?", context="The sky is blue.")
        log = llm.get_call_log()
        assert "The sky is blue." in log[0]["prompt"]

    def test_result_fields(self) -> None:
        client = CompletionClient()
        result = client.complete("test")
        assert isinstance(result, CompletionResult)
        assert isinstance(result.content, str)
        assert isinstance(result.model, str)
        assert isinstance(result.latency_ms, float)

    def test_token_counts(self) -> None:
        client = CompletionClient()
        result = client.complete("one two three")
        assert result.prompt_tokens > 0
        assert result.completion_tokens > 0
        assert result.total_tokens == result.prompt_tokens + result.completion_tokens


class TestEndpointFactory:
    """Tests for the FastAPI endpoint factory."""

    def test_create_endpoint(self) -> None:
        client = CompletionClient()
        endpoint = client.create_endpoint()
        assert "path" in endpoint
        assert "method" in endpoint
        assert "handler" in endpoint

    def test_endpoint_path(self) -> None:
        client = CompletionClient()
        endpoint = client.create_endpoint()
        assert endpoint["path"] == "/api/complete"

    def test_endpoint_method(self) -> None:
        client = CompletionClient()
        endpoint = client.create_endpoint()
        assert endpoint["method"] == "POST"

    @pytest.mark.asyncio
    async def test_handler_returns_dict(self) -> None:
        llm = MockLLM(default_response="async result")
        client = CompletionClient(llm)
        endpoint = client.create_endpoint()
        result = await endpoint["handler"]("test prompt")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_handler_has_content(self) -> None:
        llm = MockLLM(default_response="handler output")
        client = CompletionClient(llm)
        endpoint = client.create_endpoint()
        result = await endpoint["handler"]("test prompt")
        assert result["content"] == "handler output"
        assert "usage" in result
        assert "latency_ms" in result
