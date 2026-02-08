"""Base provider interface.

This module defines the abstract base class that all LLM providers must implement.
Using a common interface allows the UnifiedLLMClient to work with any provider
without knowing provider-specific details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llm_integration_starter.client import LLMResponse


class BaseProvider(ABC):
    """Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    these three core methods. This ensures consistency across providers.
    """

    @abstractmethod
    def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse containing the generated text and metadata

        Raises:
            Exception: Provider-specific errors (network, rate limit, etc.)
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using provider-specific tokenizer.

        Args:
            text: Input text to tokenize

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in dollars
        """
        pass
