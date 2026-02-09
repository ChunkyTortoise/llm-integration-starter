# Demo Mode Guide

## Overview
Run llm-integration-starter without API keys or external LLM services using the built-in **mock provider**. Perfect for testing, development, and learning without costs.

## Quick Start

### CLI Demo
```bash
# No API keys needed
llm-starter chat "What is AI?" --provider mock

# Compare mock responses
llm-starter compare --providers mock "Explain machine learning"

# Benchmark performance
llm-starter benchmark --provider mock --n-requests 100
```

### Python API Demo
```python
from llm_integration_starter import UnifiedLLMClient

# Create client with mock provider
client = UnifiedLLMClient(provider="mock")

# Send messages (no API key required)
messages = [{"role": "user", "content": "Hello!"}]
response = client.complete(messages)

print(f"Response: {response.text}")
print(f"Tokens: {response.input_tokens} in, {response.output_tokens} out")
print(f"Cost: ${response.cost:.4f}")
print(f"Latency: {response.latency_ms:.0f}ms")
```

### Streaming Demo
```python
client = UnifiedLLMClient(provider="mock")

for chunk in client.stream(messages):
    print(chunk.delta, end="", flush=True)
print()
```

## What's Mocked

### Mock Provider Behavior
The mock provider (`llm_integration_starter/providers/mock.py`) provides **deterministic responses** without API calls:

#### Response Generation
- **Echoes input**: Returns a modified version of your last message
- **Adds prefix**: `"Mock response to: [your message]"`
- **Deterministic**: Same input always produces same output
- **No randomness**: Temperature parameter is ignored

#### Token Counting
- **Input tokens**: Character count / 4 (approximates GPT tokenization)
- **Output tokens**: Response length / 4
- **Cost**: Always $0.00 (no real API calls)

#### Latency Simulation
- **Artificial delay**: Sleeps 50-150ms to simulate network latency
- **Configurable**: Set `MOCK_LATENCY_MS` environment variable
- **Realistic timing**: Helps test timeout and retry logic

#### Metadata
```python
response.provider  # "mock"
response.model     # "mock-model-v1"
response.latency_ms  # 50-150ms simulated
response.cached    # Always False
```

### Function Calling Mock
```python
from llm_integration_starter.function_calling import ToolDefinition

# Define a tool
weather_tool = ToolDefinition(
    name="get_weather",
    description="Get weather",
    parameters={...}
)

# Mock will "use" the tool automatically if present
response = client.complete(messages, tools=[weather_tool])

# Check for tool calls
if response.tool_calls:
    call = response.tool_calls[0]
    print(f"Tool: {call.name}")
    print(f"Args: {call.arguments}")
```

Mock provider generates a synthetic tool call with plausible arguments based on the tool schema.

## Switching to Production

### 1. Set Up API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Add real API keys:
```bash
# Claude (Anthropic)
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# OpenAI
OPENAI_API_KEY=sk-xxx

# Google Gemini
GOOGLE_API_KEY=AIzaSyxxx
```

### 2. Switch Provider
```bash
# Command line
llm-starter chat "Hello" --provider claude

# Python
client = UnifiedLLMClient(provider="claude")
response = client.complete(messages)
```

### 3. Enable Production Features

#### Caching
```python
from llm_integration_starter.cache import LRUCache

cache = LRUCache(max_size=500, ttl_seconds=3600)
client = UnifiedLLMClient(provider="claude", cache=cache)
```

#### Retry Logic
```python
from llm_integration_starter.retry import RetryPolicy

policy = RetryPolicy(max_attempts=3, initial_delay=1.0)
client = UnifiedLLMClient(provider="claude", retry_policy=policy)
```

#### Fallback Chain
```python
from llm_integration_starter.fallback import FallbackChain

chain = FallbackChain(providers=["claude", "openai", "gemini"])
result = chain.complete(messages)
```

#### Cost Tracking
```python
from llm_integration_starter.cost_tracker import CostTracker

tracker = CostTracker()
response = client.complete(messages)
tracker.track(response)

print(f"Total cost: ${tracker.get_total_cost():.2f}")
```

### 4. Production Deployment Checklist
- Set `DEFAULT_PROVIDER=claude` in `.env`
- Enable retry policy and circuit breaker
- Configure caching with appropriate TTL
- Set up cost tracking and alerts
- Add request logging for debugging
- Implement rate limiting (if needed)
- Use HTTPS for all API calls (handled by httpx)

## Environment Variables

Demo mode requires **no environment variables**. For production:

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | For Claude | Anthropic API authentication |
| `OPENAI_API_KEY` | For OpenAI | OpenAI API authentication |
| `GOOGLE_API_KEY` | For Gemini | Google Gemini API authentication |
| `DEFAULT_PROVIDER` | Optional | Default provider (default: mock) |
| `DEFAULT_MODEL` | Optional | Default model name |
| `MOCK_LATENCY_MS` | Optional | Mock provider latency (default: 50-150ms) |

### Example Production .env
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=AIzaSyxxx
DEFAULT_PROVIDER=claude
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

## Performance Benchmarks (Demo Mode)

On a standard laptop:
- **Completion**: 50-150ms per request (simulated latency)
- **Streaming**: ~10ms per chunk
- **Batch processing**: 100 requests in ~5 seconds (with mock provider)
- **Memory**: <50MB for client + cache
- **Throughput**: ~1,000 requests/second (no rate limits in mock)

## Testing Patterns

### Unit Tests with Mock Provider
```python
# test_my_feature.py
from llm_integration_starter import UnifiedLLMClient

def test_my_feature():
    client = UnifiedLLMClient(provider="mock")
    messages = [{"role": "user", "content": "test"}]
    response = client.complete(messages)

    assert response.text.startswith("Mock response")
    assert response.provider == "mock"
    assert response.cost == 0.0
```

### Integration Tests (Production Providers)
```python
import os
import pytest

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="No API key"
)
def test_claude_integration():
    client = UnifiedLLMClient(provider="claude")
    response = client.complete([{"role": "user", "content": "hi"}])
    assert response.provider == "claude"
    assert len(response.text) > 0
```

## Security Checklist

Demo mode is safe for public use:
- No API keys required
- No network calls (mock provider)
- No sensitive data transmitted
- No cost accumulation

For production:
- **Never commit API keys**: Use `.env` files (gitignored)
- **Rotate keys regularly**: Especially if compromised
- **Use environment variables**: Not hardcoded strings
- **Enable rate limiting**: Prevent abuse and cost overruns
- **Log carefully**: Don't log API keys or sensitive prompts
- **Validate inputs**: Sanitize user messages before sending to LLMs
- **Monitor costs**: Set up alerts for unexpected spending
