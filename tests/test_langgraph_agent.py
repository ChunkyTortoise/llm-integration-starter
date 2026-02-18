"""Tests for LangGraphReActAgent."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from llm_integration_starter.agents.base import AgentResult
from llm_integration_starter.agents.langgraph_agent import (
    LangGraphReActAgent,
    _callable_to_tool_def,
    _LANGGRAPH_AVAILABLE,
)
from llm_integration_starter.client import LLMResponse, UnifiedLLMClient
from llm_integration_starter.function_calling import ToolDefinition


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def _mock_response(text: str = "Final answer.", tool_calls: list | None = None) -> MagicMock:
    """Build a mock LLMResponse with optional tool_calls in .raw."""
    response = MagicMock(spec=LLMResponse)
    response.text = text
    response.raw = {"tool_calls": tool_calls or []}
    response.input_tokens = 10
    response.output_tokens = 20
    response.cost = 0.0
    return response


@pytest.fixture
def mock_client():
    return UnifiedLLMClient(provider="mock")


# ---------------------------------------------------------------------------
# _callable_to_tool_def helper
# ---------------------------------------------------------------------------


class TestCallableToToolDef:
    def test_returns_tool_definition(self):
        td = _callable_to_tool_def("add", add)
        assert isinstance(td, ToolDefinition)
        assert td.name == "add"

    def test_uses_docstring_as_description(self):
        td = _callable_to_tool_def("add", add)
        assert "Add two integers" in td.description

    def test_parameters_from_signature(self):
        td = _callable_to_tool_def("add", add)
        props = td.parameters.get("properties", {})
        assert "a" in props
        assert "b" in props
        assert props["a"]["type"] == "integer"
        assert props["b"]["type"] == "integer"

    def test_required_params_captured(self):
        td = _callable_to_tool_def("add", add)
        assert "a" in td.parameters.get("required", [])
        assert "b" in td.parameters.get("required", [])

    def test_string_param_type(self):
        td = _callable_to_tool_def("greet", greet)
        props = td.parameters.get("properties", {})
        assert props["name"]["type"] == "string"

    def test_fallback_description_when_no_docstring(self):
        def no_doc():
            pass

        td = _callable_to_tool_def("no_doc", no_doc)
        assert td.description == "Execute no_doc"


# ---------------------------------------------------------------------------
# LangGraphReActAgent construction
# ---------------------------------------------------------------------------


class TestLangGraphReActAgentInit:
    def test_no_args_uses_mock_client(self):
        agent = LangGraphReActAgent()
        assert agent.client is not None

    def test_tools_registered(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client, tools={"add": add})
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "add"

    def test_no_tools_gives_empty_list(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        assert agent.tools == []

    def test_custom_max_iterations(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client, max_iterations=5)
        assert agent.max_iterations == 5

    def test_graph_built_when_langgraph_available(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        if _LANGGRAPH_AVAILABLE:
            assert agent._graph is not None
        else:
            assert agent._graph is None


# ---------------------------------------------------------------------------
# system_prompt property
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_default_includes_tool_names(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client, tools={"add": add, "greet": greet})
        assert "add" in agent.system_prompt
        assert "greet" in agent.system_prompt

    def test_default_without_tools_says_none(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        assert "none" in agent.system_prompt.lower()

    def test_override_system_prompt(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client, system_prompt="Custom prompt")
        assert agent.system_prompt == "Custom prompt"


# ---------------------------------------------------------------------------
# run() — final answer path (no tool calls)
# ---------------------------------------------------------------------------


class TestRunNoToolCalls:
    def test_returns_agent_result(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        result = agent.run("What is 2+2?")
        assert isinstance(result, AgentResult)

    def test_output_is_string(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        result = agent.run("Hello")
        assert isinstance(result.output, str)

    def test_metadata_has_langgraph_flag(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        result = agent.run("Hello")
        assert "langgraph_available" in result.metadata

    def test_metadata_iterations_zero_when_no_tools_used(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        result = agent.run("Hello")
        # No tool calls executed → tool_results empty → iterations == 0
        assert result.metadata.get("iterations", 0) == 0

    def test_run_with_history(self, mock_client):
        agent = LangGraphReActAgent(client=mock_client)
        history = [{"role": "user", "content": "previous"}, {"role": "assistant", "content": "reply"}]
        result = agent.run("Follow-up question", history=history)
        assert isinstance(result, AgentResult)


# ---------------------------------------------------------------------------
# run() — tool call path
# ---------------------------------------------------------------------------


class TestRunWithToolCalls:
    def _make_tool_call(self, name: str, args: dict) -> dict:
        return {"function": {"name": name, "arguments": json.dumps(args)}}

    def test_tool_is_invoked(self, mock_client):
        tool_call = self._make_tool_call("add", {"a": 10, "b": 32})

        call_count = {"n": 0}

        def side_effect(messages, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _mock_response("", tool_calls=[tool_call])
            return _mock_response("The answer is 42.")

        mock_client._provider_instance.complete = side_effect

        agent = LangGraphReActAgent(client=mock_client, tools={"add": add})
        result = agent.run("What is 10 + 32?")

        assert isinstance(result, AgentResult)
        assert result.metadata["iterations"] >= 1

    def test_tools_used_tracked_in_metadata(self, mock_client):
        tool_call = self._make_tool_call("add", {"a": 1, "b": 2})
        call_count = {"n": 0}

        def side_effect(messages, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _mock_response("", tool_calls=[tool_call])
            return _mock_response("Done.")

        mock_client._provider_instance.complete = side_effect

        agent = LangGraphReActAgent(client=mock_client, tools={"add": add})
        result = agent.run("Add 1 and 2")

        assert "add" in result.metadata.get("tools_used", [])

    def test_unknown_tool_returns_error_message(self, mock_client):
        tool_call = self._make_tool_call("nonexistent_tool", {})
        call_count = {"n": 0}

        def side_effect(messages, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _mock_response("", tool_calls=[tool_call])
            return _mock_response("Could not help.")

        mock_client._provider_instance.complete = side_effect

        # Should not raise — unknown tool returns error string appended to messages
        agent = LangGraphReActAgent(client=mock_client)
        result = agent.run("Use nonexistent tool")
        assert isinstance(result, AgentResult)

    def test_tool_exception_is_caught(self, mock_client):
        def broken_tool() -> str:
            """A tool that always raises."""
            raise RuntimeError("Oops")

        tool_call = {"function": {"name": "broken", "arguments": "{}"}}
        call_count = {"n": 0}

        def side_effect(messages, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _mock_response("", tool_calls=[tool_call])
            return _mock_response("Handled.")

        mock_client._provider_instance.complete = side_effect

        agent = LangGraphReActAgent(client=mock_client, tools={"broken": broken_tool})
        result = agent.run("Trigger broken tool")
        assert isinstance(result, AgentResult)


# ---------------------------------------------------------------------------
# max_iterations safety cap
# ---------------------------------------------------------------------------


class TestMaxIterations:
    def test_terminates_after_max_iterations(self, mock_client):
        """Agent must stop even if LLM keeps returning tool calls."""
        tool_call = {"function": {"name": "add", "arguments": '{"a": 1, "b": 2}'}}

        def always_tool_call(messages, **kwargs):
            return _mock_response("", tool_calls=[tool_call])

        mock_client._provider_instance.complete = always_tool_call

        agent = LangGraphReActAgent(client=mock_client, tools={"add": add}, max_iterations=3)
        result = agent.run("Loop forever")

        # Should complete (not infinite loop) and iterations capped
        assert isinstance(result, AgentResult)
        assert result.metadata.get("iterations", 0) <= 3


# ---------------------------------------------------------------------------
# Fallback path (LangGraph unavailable)
# ---------------------------------------------------------------------------


class TestFallbackPath:
    def test_fallback_returns_agent_result(self, mock_client):
        with patch("llm_integration_starter.agents.langgraph_agent._LANGGRAPH_AVAILABLE", False):
            agent = LangGraphReActAgent(client=mock_client)
            agent._graph = None  # Ensure graph not used
            result = agent.run("Hello without langgraph")
            assert isinstance(result, AgentResult)

    def test_fallback_metadata_flags(self, mock_client):
        with patch("llm_integration_starter.agents.langgraph_agent._LANGGRAPH_AVAILABLE", False):
            agent = LangGraphReActAgent(client=mock_client)
            agent._graph = None
            result = agent.run("Hello")
            assert result.metadata.get("langgraph_available") is False
            assert result.metadata.get("fallback") is True
