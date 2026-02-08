"""llm-integration-starter: Production-ready LLM integration patterns."""

__version__ = "0.1.0"

from llm_starter.completion import CompletionClient, CompletionResult
from llm_starter.cost_tracker import CostRecord, CostSummary, CostTracker
from llm_starter.function_calling import FunctionCallingClient, ToolCallResult, ToolDefinition
from llm_starter.hardening import CircuitBreaker, HardenedClient
from llm_starter.latency_tracker import LatencyStats, LatencyTracker
from llm_starter.mock_llm import MockLLM, MockResponse
from llm_starter.rag_pipeline import RAGResult, SimpleRAG
from llm_starter.streaming import StreamEvent, StreamingClient

__all__ = [
    "MockLLM",
    "MockResponse",
    "CompletionClient",
    "CompletionResult",
    "StreamingClient",
    "StreamEvent",
    "FunctionCallingClient",
    "ToolDefinition",
    "ToolCallResult",
    "SimpleRAG",
    "RAGResult",
    "CircuitBreaker",
    "HardenedClient",
    "CostTracker",
    "CostRecord",
    "CostSummary",
    "LatencyTracker",
    "LatencyStats",
]
