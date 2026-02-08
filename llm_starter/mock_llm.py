"""Mock LLM provider for testing and demos without API keys."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class MockResponse:
    """Simulated LLM response."""

    content: str
    model: str = "mock-gpt-4"
    usage: dict[str, int] = field(
        default_factory=lambda: {
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "total_tokens": 80,
        }
    )
    latency_ms: float = 0.0
    tool_calls: list[dict] | None = None


class MockLLM:
    """Mock LLM that returns deterministic responses for testing.

    Supports: complete, stream, function_call.
    No API keys needed.
    """

    def __init__(
        self,
        default_response: str = "This is a mock response.",
        latency_ms: float = 10.0,
    ):
        self.default_response = default_response
        self.latency_ms = latency_ms
        self._responses: dict[str, str] = {}
        self._call_log: list[dict] = []

    def set_response(self, prompt_contains: str, response: str) -> None:
        """Set a canned response for prompts containing a keyword."""
        self._responses[prompt_contains.lower()] = response

    def complete(
        self,
        prompt: str,
        model: str = "mock-gpt-4",
        max_tokens: int = 500,
    ) -> MockResponse:
        """Simulate a completion call."""
        start = time.perf_counter()

        # Find matching canned response
        response_text = self.default_response
        for keyword, resp in self._responses.items():
            if keyword in prompt.lower():
                response_text = resp
                break

        # Simulate latency
        elapsed = (time.perf_counter() - start) * 1000 + self.latency_ms

        self._call_log.append({"prompt": prompt, "model": model, "response": response_text})

        prompt_tokens = len(prompt.split()) * 2  # rough estimate
        completion_tokens = len(response_text.split()) * 2

        return MockResponse(
            content=response_text,
            model=model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            latency_ms=round(elapsed, 2),
        )

    def stream(self, prompt: str, model: str = "mock-gpt-4") -> list[str]:
        """Simulate streaming by returning words as chunks."""
        response = self.complete(prompt, model)
        return response.content.split()

    def function_call(
        self,
        prompt: str,
        tools: list[dict],
        model: str = "mock-gpt-4",
    ) -> MockResponse:
        """Simulate a function call response."""
        # Pick the first tool as the mock call
        if tools:
            tool = tools[0]
            tool_name = tool.get("name", tool.get("function", {}).get("name", "unknown"))
            tool_call = {
                "name": tool_name,
                "arguments": {"query": prompt[:50]},
                "id": f"call_{len(self._call_log)}",
            }
            return MockResponse(
                content="",
                model=model,
                tool_calls=[tool_call],
            )
        return self.complete(prompt, model)

    def get_call_log(self) -> list[dict]:
        """Get all recorded calls."""
        return self._call_log.copy()

    def reset(self) -> None:
        """Reset call log and canned responses."""
        self._call_log.clear()
        self._responses.clear()
