"""Tests for FunctionCallingClient and demo tools."""

from __future__ import annotations

from llm_starter.function_calling import (
    FunctionCallingClient,
    ToolCallResult,
    ToolDefinition,
)
from llm_starter.mock_llm import MockLLM


class TestFunctionCallingClient:
    """Tests for FunctionCallingClient."""

    def test_demo_tools_registered(self) -> None:
        client = FunctionCallingClient()
        tools = client.get_tools()
        names = [t.name for t in tools]
        assert "calculate" in names
        assert "lookup" in names
        assert "format_data" in names

    def test_get_tool_schemas(self) -> None:
        client = FunctionCallingClient()
        schemas = client.get_tool_schemas()
        assert len(schemas) >= 3
        assert all("name" in s for s in schemas)
        assert all("description" in s for s in schemas)

    def test_register_custom_tool(self) -> None:
        client = FunctionCallingClient()
        custom = ToolDefinition(
            name="custom",
            description="Custom tool",
            parameters={"type": "object"},
            handler=lambda: "custom result",
        )
        client.register_tool(custom)
        names = [t.name for t in client.get_tools()]
        assert "custom" in names

    def test_execute_calculate(self) -> None:
        client = FunctionCallingClient()
        result = client.execute_tool("calculate", {"expression": "2 + 3"})
        assert result.result == "5"
        assert result.error is None

    def test_execute_lookup(self) -> None:
        client = FunctionCallingClient()
        result = client.execute_tool("lookup", {"query": "python"})
        assert "Python" in result.result

    def test_execute_format(self) -> None:
        client = FunctionCallingClient()
        result = client.execute_tool("format_data", {"data": "hello", "format": "json"})
        assert "hello" in result.result

    def test_execute_unknown_tool(self) -> None:
        client = FunctionCallingClient()
        result = client.execute_tool("nonexistent", {"arg": "val"})
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_process_pipeline(self) -> None:
        llm = MockLLM()
        client = FunctionCallingClient(llm)
        results = client.process("calculate something")
        assert len(results) >= 1
        assert isinstance(results[0], ToolCallResult)


class TestDemoFunctions:
    """Tests for demo function implementations."""

    def test_calculate_basic(self) -> None:
        result = FunctionCallingClient._demo_calculate(expression="10 * 5")
        assert result == "50"

    def test_calculate_invalid(self) -> None:
        result = FunctionCallingClient._demo_calculate(expression="import os")
        assert result == "Invalid expression"

    def test_lookup_known(self) -> None:
        result = FunctionCallingClient._demo_lookup(query="What is AI?")
        assert "Artificial Intelligence" in result

    def test_lookup_unknown(self) -> None:
        result = FunctionCallingClient._demo_lookup(query="quantum computing")
        assert "No fact found" in result
