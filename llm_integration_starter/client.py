"""Unified LLM client."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    pass

from llm_integration_starter.providers.base import BaseProvider
from llm_integration_starter.providers.mock import MockProvider


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    provider: str
    model: str

class UnifiedLLMClient:
    _providers: dict[str, type[BaseProvider]] = {"mock": MockProvider}

    def __init__(self, provider: str = "mock", model: str | None = None, **provider_kwargs):
        if provider not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ValueError(f"Unknown provider '{provider}'. Available: {available}")
        self.provider_name = provider
        self.model = model
        self._provider_instance = self._providers[provider](**provider_kwargs)

    def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        return self._provider_instance.complete(messages, **kwargs)

    def complete_with_tools(self, messages: list[dict], tools: list, **kwargs) -> LLMResponse:
        raise NotImplementedError("Function calling not yet implemented")

    def stream(self, messages: list[dict], **kwargs) -> Iterator:
        raise NotImplementedError("Streaming not yet implemented")

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    @property
    def provider(self) -> BaseProvider:
        return self._provider_instance
