"""Function calling abstraction."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict

    @classmethod
    def create(cls, name: str, description: str, properties: dict, required: list[str] | None = None):
        parameters = {"type": "object", "properties": properties, "required": required or []}
        return cls(name=name, description=description, parameters=parameters)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


class FunctionCallingFormatter:
    def format_tools(self, tools: list[ToolDefinition], provider: str) -> list[dict]:
        if provider == "claude":
            return self._format_claude_tools(tools)
        elif provider == "openai":
            return self._format_openai_tools(tools)
        elif provider == "gemini":
            return self._format_gemini_tools(tools)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _format_claude_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]

    def _format_openai_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
            for t in tools
        ]

    def _format_gemini_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "function_declarations": [
                    {"name": t.name, "description": t.description, "parameters": t.parameters} for t in tools
                ]
            }
        ]

    def parse_tool_calls(self, response: dict, provider: str) -> list[ToolCall]:
        if provider == "claude":
            return self._parse_claude_tool_calls(response)
        elif provider == "openai":
            return self._parse_openai_tool_calls(response)
        elif provider == "gemini":
            return self._parse_gemini_tool_calls(response)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _parse_claude_tool_calls(self, response: dict) -> list[ToolCall]:
        tool_calls = []
        for block in response.get("content", []):
            if block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.get("id", ""), name=block.get("name", ""), arguments=block.get("input", {}))
                )
        return tool_calls

    def _parse_openai_tool_calls(self, response: dict) -> list[ToolCall]:
        tool_calls = []
        message = response.get("choices", [{}])[0].get("message", {})
        for call in message.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=call.get("id", ""),
                    name=call.get("function", {}).get("name", ""),
                    arguments=json.loads(call.get("function", {}).get("arguments", "{}")),
                )
            )
        return tool_calls

    def _parse_gemini_tool_calls(self, response: dict) -> list[ToolCall]:
        tool_calls = []
        candidates = response.get("candidates", [])
        if candidates:
            for part in candidates[0].get("content", {}).get("parts", []):
                if "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(
                        ToolCall(id=fc.get("name", ""), name=fc.get("name", ""), arguments=fc.get("args", {}))
                    )
        return tool_calls
