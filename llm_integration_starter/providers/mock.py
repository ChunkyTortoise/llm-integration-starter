"""Mock provider for testing."""
from __future__ import annotations

import time

from llm_integration_starter.providers.base import BaseProvider


class MockProvider(BaseProvider):
    def __init__(self, default_response: str = "Mock response", latency_ms: float = 100.0,
                 input_cost_per_1k: float = 0.001, output_cost_per_1k: float = 0.002):
        self.default_response = default_response
        self.latency_ms = latency_ms
        self.input_cost_per_1k = input_cost_per_1k
        self.output_cost_per_1k = output_cost_per_1k

    def complete(self, messages: list[dict], **kwargs):
        # Import here to avoid circular dependency
        from llm_integration_starter.client import LLMResponse

        start = time.perf_counter()
        time.sleep(self.latency_ms / 1000.0)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        input_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in messages)
        output_tokens = self.count_tokens(self.default_response)
        cost = self.estimate_cost(input_tokens, output_tokens)
        return LLMResponse(
            text=self.default_response, input_tokens=input_tokens,
            output_tokens=output_tokens, cost=cost, latency_ms=elapsed_ms,
            provider="mock", model="mock-model"
        )

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000.0) * self.input_cost_per_1k + (output_tokens / 1000.0) * self.output_cost_per_1k
