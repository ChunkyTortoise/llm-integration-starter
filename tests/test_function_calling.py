"""Tests for function calling abstraction."""

from __future__ import annotations

import pytest

from llm_integration_starter.function_calling import FunctionCallingFormatter, ToolCall, ToolDefinition


class TestToolDefinition:
    """Tests for ToolDefinition."""

    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="test_func",
            description="Test function",
            parameters={"type": "object", "properties": {}},
        )
        assert tool.name == "test_func"
        assert tool.description == "Test function"

    def test_tool_definition_create_helper(self):
        """Test create() helper method."""
        tool = ToolDefinition.create(
            name="get_weather",
            description="Get weather",
            properties={"location": {"type": "string"}},
            required=["location"],
        )
        assert tool.name == "get_weather"
        assert tool.parameters["type"] == "object"
        assert "location" in tool.parameters["properties"]
        assert "location" in tool.parameters["required"]

    def test_tool_definition_without_required(self):
        """Test creating tool without required parameters."""
        tool = ToolDefinition.create(
            name="test",
            description="Test",
            properties={"param": {"type": "string"}},
        )
        assert tool.parameters["required"] == []


class TestToolCall:
    """Tests for ToolCall."""

    def test_tool_call_creation(self):
        """Test creating a tool call."""
        call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"location": "NYC"},
        )
        assert call.id == "call_123"
        assert call.name == "get_weather"
        assert call.arguments == {"location": "NYC"}


class TestFunctionCallingFormatter:
    """Tests for FunctionCallingFormatter."""

    def test_formatter_initialization(self):
        """Test creating a formatter."""
        formatter = FunctionCallingFormatter()
        assert formatter is not None

    def test_format_tools_for_claude(self):
        """Test formatting tools for Claude."""
        formatter = FunctionCallingFormatter()
        tool = ToolDefinition.create(
            name="search",
            description="Search function",
            properties={"query": {"type": "string"}},
        )

        formatted = formatter.format_tools([tool], "claude")
        assert len(formatted) == 1
        assert formatted[0]["name"] == "search"
        assert "input_schema" in formatted[0]

    def test_format_tools_for_openai(self):
        """Test formatting tools for OpenAI."""
        formatter = FunctionCallingFormatter()
        tool = ToolDefinition.create(
            name="search",
            description="Search function",
            properties={"query": {"type": "string"}},
        )

        formatted = formatter.format_tools([tool], "openai")
        assert len(formatted) == 1
        assert formatted[0]["type"] == "function"
        assert "function" in formatted[0]
        assert formatted[0]["function"]["name"] == "search"

    def test_format_tools_for_gemini(self):
        """Test formatting tools for Gemini."""
        formatter = FunctionCallingFormatter()
        tool = ToolDefinition.create(
            name="search",
            description="Search function",
            properties={"query": {"type": "string"}},
        )

        formatted = formatter.format_tools([tool], "gemini")
        assert len(formatted) == 1
        assert "function_declarations" in formatted[0]

    def test_format_tools_unknown_provider(self):
        """Test formatting tools for unknown provider raises error."""
        formatter = FunctionCallingFormatter()
        tool = ToolDefinition.create(name="test", description="Test", properties={})

        with pytest.raises(ValueError, match="Unknown provider"):
            formatter.format_tools([tool], "unknown")

    def test_parse_claude_tool_calls(self):
        """Test parsing Claude tool calls."""
        formatter = FunctionCallingFormatter()
        response = {
            "content": [
                {"type": "tool_use", "id": "call_1", "name": "search", "input": {"query": "test"}},
            ]
        }

        calls = formatter.parse_tool_calls(response, "claude")
        assert len(calls) == 1
        assert calls[0].name == "search"
        assert calls[0].arguments == {"query": "test"}

    def test_parse_openai_tool_calls(self):
        """Test parsing OpenAI tool calls."""
        formatter = FunctionCallingFormatter()
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {"name": "search", "arguments": '{"query": "test"}'},
                            }
                        ]
                    }
                }
            ]
        }

        calls = formatter.parse_tool_calls(response, "openai")
        assert len(calls) == 1
        assert calls[0].name == "search"

    def test_parse_gemini_tool_calls(self):
        """Test parsing Gemini tool calls."""
        formatter = FunctionCallingFormatter()
        response = {
            "candidates": [{"content": {"parts": [{"functionCall": {"name": "search", "args": {"query": "test"}}}]}}]
        }

        calls = formatter.parse_tool_calls(response, "gemini")
        assert len(calls) == 1
        assert calls[0].name == "search"

    def test_parse_tool_calls_unknown_provider(self):
        """Test parsing tool calls for unknown provider raises error."""
        formatter = FunctionCallingFormatter()
        with pytest.raises(ValueError, match="Unknown provider"):
            formatter.parse_tool_calls({}, "unknown")

    def test_format_multiple_tools(self):
        """Test formatting multiple tools."""
        formatter = FunctionCallingFormatter()
        tools = [
            ToolDefinition.create("tool1", "First tool", {"p1": {"type": "string"}}),
            ToolDefinition.create("tool2", "Second tool", {"p2": {"type": "number"}}),
        ]

        formatted = formatter.format_tools(tools, "claude")
        assert len(formatted) == 2
