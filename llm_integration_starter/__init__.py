"""LLM Integration Starter Kit.

A beginner-friendly learning kit for integrating multiple LLM providers
with a unified interface. Demonstrates:
- Client abstraction across providers
- Streaming responses
- Function calling
- Retry logic with circuit breakers
- Fallback chains
- Caching
- Cost tracking
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "ChunkyTortoise"

from llm_integration_starter.cache import LRUCache
from llm_integration_starter.client import LLMResponse, UnifiedLLMClient
from llm_integration_starter.cost_tracker import CostEntry, CostTracker
from llm_integration_starter.fallback import FallbackChain, FallbackResult
from llm_integration_starter.function_calling import FunctionCallingFormatter, ToolCall, ToolDefinition
from llm_integration_starter.guardrails import (
    ContentFilter,
    GuardrailPolicy,
    GuardrailsEngine,
    InjectionPattern,
    PIIDetector,
    PIIMatch,
    PromptInjectionDetector,
    SafetyReport,
)
from llm_integration_starter.retry import CircuitBreaker, RetryPolicy
from llm_integration_starter.streaming import StreamDelta, StreamingParser

__all__ = [
    "ContentFilter",
    "GuardrailPolicy",
    "GuardrailsEngine",
    "InjectionPattern",
    "PIIDetector",
    "PIIMatch",
    "PromptInjectionDetector",
    "SafetyReport",
    "UnifiedLLMClient",
    "LLMResponse",
    "StreamDelta",
    "StreamingParser",
    "ToolDefinition",
    "ToolCall",
    "FunctionCallingFormatter",
    "RetryPolicy",
    "CircuitBreaker",
    "FallbackChain",
    "FallbackResult",
    "LRUCache",
    "CostTracker",
    "CostEntry",
]
