"""Fallback chain for provider redundancy."""

from __future__ import annotations

from dataclasses import dataclass, field

from llm_integration_starter.client import LLMResponse, UnifiedLLMClient


@dataclass
class FallbackResult:
    response: LLMResponse
    successful_provider: str
    attempts: int
    errors: list[str] = field(default_factory=list)


class FallbackChain:
    def __init__(self, providers: list[str], provider_kwargs: dict | None = None):
        self.providers = providers
        self.provider_kwargs = provider_kwargs or {}
        if not providers:
            raise ValueError("Must specify at least one provider")

    def execute(self, messages: list[dict], **kwargs) -> FallbackResult:
        errors = []
        last_exception = None
        for i, provider_name in enumerate(self.providers):
            try:
                client = UnifiedLLMClient(provider=provider_name, **self.provider_kwargs.get(provider_name, {}))
                response = client.complete(messages, **kwargs)
                return FallbackResult(
                    response=response, successful_provider=provider_name, attempts=i + 1, errors=errors
                )
            except Exception as e:
                errors.append(f"{provider_name}: {type(e).__name__}: {e}")
                last_exception = e
                if i == len(self.providers) - 1:
                    raise last_exception
                continue
        raise RuntimeError("Fallback chain failed")

    def add_provider(self, provider: str) -> None:
        if provider not in self.providers:
            self.providers.append(provider)

    def remove_provider(self, provider: str) -> None:
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not in chain")
        if len(self.providers) == 1:
            raise ValueError("Cannot remove the last provider")
        self.providers.remove(provider)

    def get_providers(self) -> list[str]:
        return self.providers.copy()
