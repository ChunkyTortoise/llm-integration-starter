"""Basic LLM completion pattern with FastAPI endpoint factory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_starter.mock_llm import MockLLM


@dataclass
class CompletionResult:
    """Result of a completion request."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float


class CompletionClient:
    """Simple completion client wrapping a MockLLM.

    Provides a clean interface for basic LLM completions,
    plus a FastAPI endpoint factory.
    """

    def __init__(self, llm: MockLLM | None = None):
        self.llm = llm or MockLLM()

    def complete(
        self,
        prompt: str,
        system: str = "",
        model: str = "mock-gpt-4",
        max_tokens: int = 500,
    ) -> CompletionResult:
        """Run a completion."""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self.llm.complete(full_prompt, model=model, max_tokens=max_tokens)
        return CompletionResult(
            content=response.content,
            model=response.model,
            prompt_tokens=response.usage["prompt_tokens"],
            completion_tokens=response.usage["completion_tokens"],
            total_tokens=response.usage["total_tokens"],
            latency_ms=response.latency_ms,
        )

    def complete_with_context(
        self,
        prompt: str,
        context: str,
        system: str = "",
    ) -> CompletionResult:
        """Run a completion with additional context prepended."""
        augmented = f"Context: {context}\n\nQuestion: {prompt}"
        return self.complete(augmented, system=system)

    def create_endpoint(self) -> dict[str, Any]:
        """Create a FastAPI endpoint configuration.

        Returns a dict with 'path', 'method', 'handler' that can be added to a FastAPI app.
        """
        client = self

        async def handler(
            prompt: str,
            system: str = "",
            model: str = "mock-gpt-4",
        ) -> dict:
            result = client.complete(prompt, system=system, model=model)
            return {
                "content": result.content,
                "model": result.model,
                "usage": {
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "total_tokens": result.total_tokens,
                },
                "latency_ms": result.latency_ms,
            }

        return {"path": "/api/complete", "method": "POST", "handler": handler}
