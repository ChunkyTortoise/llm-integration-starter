"""Tests for MockLLM and MockResponse."""

from __future__ import annotations

from llm_starter.mock_llm import MockLLM, MockResponse


class TestMockLLM:
    """Tests for MockLLM."""

    def test_default_response(self) -> None:
        llm = MockLLM(default_response="Hello world")
        result = llm.complete("anything")
        assert result.content == "Hello world"

    def test_canned_response(self) -> None:
        llm = MockLLM()
        llm.set_response("python", "Python is great")
        result = llm.complete("Tell me about Python")
        assert result.content == "Python is great"

    def test_call_log_recorded(self) -> None:
        llm = MockLLM()
        llm.complete("test prompt")
        log = llm.get_call_log()
        assert len(log) == 1
        assert log[0]["prompt"] == "test prompt"

    def test_stream_returns_words(self) -> None:
        llm = MockLLM(default_response="one two three")
        chunks = llm.stream("anything")
        assert chunks == ["one", "two", "three"]

    def test_function_call_returns_tool(self) -> None:
        llm = MockLLM()
        tools = [{"name": "calculate", "description": "Math", "parameters": {}}]
        result = llm.function_call("test", tools)
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "calculate"

    def test_reset_clears_state(self) -> None:
        llm = MockLLM()
        llm.set_response("key", "value")
        llm.complete("test")
        llm.reset()
        assert llm.get_call_log() == []
        # Canned responses should be cleared
        result = llm.complete("key")
        assert result.content == "This is a mock response."

    def test_latency_recorded(self) -> None:
        llm = MockLLM(latency_ms=5.0)
        result = llm.complete("test")
        assert result.latency_ms >= 5.0

    def test_usage_tokens(self) -> None:
        llm = MockLLM()
        result = llm.complete("hello world")
        assert result.usage["prompt_tokens"] > 0
        assert result.usage["completion_tokens"] > 0
        assert result.usage["total_tokens"] == (
            result.usage["prompt_tokens"] + result.usage["completion_tokens"]
        )


class TestMockResponse:
    """Tests for MockResponse dataclass."""

    def test_fields_present(self) -> None:
        resp = MockResponse(content="test")
        assert resp.content == "test"
        assert resp.model == "mock-gpt-4"
        assert resp.latency_ms == 0.0

    def test_default_values(self) -> None:
        resp = MockResponse(content="test")
        assert resp.usage["total_tokens"] == 80
        assert resp.tool_calls is None
