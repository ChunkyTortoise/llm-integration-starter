"""Token counting utilities."""
from __future__ import annotations


class TokenCounter:
    CHARS_PER_TOKEN = 4

    @staticmethod
    def count_tokens(text: str, provider: str = "mock") -> int:
        if provider == "mock":
            return len(text.split())
        return len(text) // TokenCounter.CHARS_PER_TOKEN

    @staticmethod
    def count_message_tokens(messages: list[dict], provider: str = "mock") -> int:
        total = 0
        for message in messages:
            content = message.get("content", "")
            total += TokenCounter.count_tokens(content, provider)
            if provider == "openai":
                total += 4
            elif provider == "claude":
                total += 3
            else:
                total += 2
        total += 3
        return total

    @staticmethod
    def estimate_cost(input_tokens: int, output_tokens: int, provider: str, model: str) -> float:
        pricing = {
            "claude": {"claude-3-opus": (15.0, 75.0), "claude-3-sonnet": (3.0, 15.0), "claude-3-haiku": (0.25, 1.25)},
            "openai": {"gpt-4-turbo": (10.0, 30.0), "gpt-4": (30.0, 60.0), "gpt-3.5-turbo": (0.5, 1.5)},
            "gemini": {"gemini-pro": (0.5, 1.5), "gemini-ultra": (10.0, 30.0)},
            "mock": {"mock-model": (0.001, 0.002)},
        }
        provider_pricing = pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, (0.0, 0.0))
        input_price, output_price = model_pricing
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        return input_cost + output_cost
