"""Function calling pattern: tool definitions, execution, and demo functions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from llm_starter.mock_llm import MockLLM


@dataclass
class ToolDefinition:
    """A tool/function that the LLM can call."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any] | None = None


@dataclass
class ToolCallResult:
    """Result of executing a tool call."""

    tool_name: str
    arguments: dict[str, Any]
    result: Any
    error: str | None = None


class FunctionCallingClient:
    """Function calling client with tool registration and execution."""

    def __init__(self, llm: MockLLM | None = None):
        self.llm = llm or MockLLM()
        self._tools: dict[str, ToolDefinition] = {}
        self._register_demo_tools()

    def _register_demo_tools(self) -> None:
        """Register 3 demo functions."""
        self.register_tool(
            ToolDefinition(
                name="calculate",
                description="Evaluate a math expression",
                parameters={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                },
                handler=self._demo_calculate,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="lookup",
                description="Look up a fact",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                },
                handler=self._demo_lookup,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="format_data",
                description="Format data as JSON",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string"},
                        "format": {"type": "string"},
                    },
                },
                handler=self._demo_format,
            )
        )

    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_schemas(self) -> list[dict]:
        """Get tool schemas for LLM API calls."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def call_llm(self, prompt: str) -> list[dict]:
        """Call the LLM and get tool calls."""
        schemas = self.get_tool_schemas()
        response = self.llm.function_call(prompt, tools=schemas)
        return response.tool_calls or []

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolCallResult:
        """Execute a tool with given arguments."""
        tool = self._tools.get(tool_name)
        if not tool or not tool.handler:
            return ToolCallResult(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                error=f"Tool not found or no handler: {tool_name}",
            )
        try:
            result = tool.handler(**arguments)
            return ToolCallResult(tool_name=tool_name, arguments=arguments, result=result)
        except Exception as e:
            return ToolCallResult(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                error=str(e),
            )

    def process(self, prompt: str) -> list[ToolCallResult]:
        """Full pipeline: call LLM -> get tool calls -> execute tools."""
        tool_calls = self.call_llm(prompt)
        results = []
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("arguments", {})
            results.append(self.execute_tool(name, args))
        return results

    @staticmethod
    def _demo_calculate(expression: str = "", **kwargs: Any) -> str:
        """Demo: safe math evaluation."""
        try:
            # Only allow basic math operations
            allowed = set("0123456789+-*/.(). ")
            if all(c in allowed for c in expression):
                return str(eval(expression))  # noqa: S307
            return "Invalid expression"
        except Exception:
            return "Calculation error"

    @staticmethod
    def _demo_lookup(query: str = "", **kwargs: Any) -> str:
        """Demo: mock fact lookup."""
        facts = {
            "python": "Python is a programming language created by Guido van Rossum in 1991.",
            "earth": "Earth is the third planet from the Sun.",
            "ai": "AI stands for Artificial Intelligence.",
        }
        for key, fact in facts.items():
            if key in query.lower():
                return fact
        return f"No fact found for: {query}"

    @staticmethod
    def _demo_format(data: str = "", format: str = "json", **kwargs: Any) -> str:
        """Demo: format data."""
        try:
            parsed = (
                json.loads(data) if data.startswith("{") or data.startswith("[") else {"text": data}
            )
            if format == "json":
                return json.dumps(parsed, indent=2)
            return str(parsed)
        except Exception:
            return json.dumps({"text": data})
