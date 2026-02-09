# Customization Guide

## Quick Start (5 minutes)

### Environment Setup
```bash
git clone https://github.com/ChunkyTortoise/llm-integration-starter.git
cd llm-integration-starter
pip install -e .
cp .env.example .env
```

### First Run (No API Keys Needed)
```bash
# Use mock provider for testing
llm-starter chat "Hello, world!" --provider mock

# Run all 76 tests
make test

# Launch Streamlit demo (if available)
make demo
```

### Add API Keys for Real Providers
Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-xxx  # Get from console.anthropic.com
OPENAI_API_KEY=sk-xxx         # Get from platform.openai.com
GOOGLE_API_KEY=xxx            # Get from makersuite.google.com
```

Verify:
```bash
llm-starter chat "What is 2+2?" --provider claude
```

## Common Customizations

### 1. Provider Configuration
**Default Provider** (`.env`):
```bash
DEFAULT_PROVIDER=claude
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

**Custom Provider** (`llm_integration_starter/providers/custom.py`):
```python
from llm_integration_starter.providers.base import BaseProvider, LLMResponse

class CustomProvider(BaseProvider):
    def complete(self, messages, **kwargs):
        # Your custom implementation
        response = your_api_call(messages, **kwargs)
        return LLMResponse(
            text=response["output"],
            provider="custom",
            model="custom-model-v1",
            input_tokens=response["usage"]["input"],
            output_tokens=response["usage"]["output"]
        )
```

Register in `client.py`, line 30:
```python
from llm_integration_starter.providers.custom import CustomProvider

PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "mock": MockProvider,
    "custom": CustomProvider,  # Add this
}
```

### 2. Retry & Circuit Breaker
**Retry Policy** (`llm_integration_starter/retry.py`, line 20):
```python
policy = RetryPolicy(
    max_attempts=5,        # Up from default 3
    initial_delay=2.0,     # Start with 2 seconds
    max_delay=60.0,        # Cap at 1 minute
    exponential_base=3.0,  # Faster backoff
    jitter=True            # Randomize delays
)
```

**Circuit Breaker Thresholds** (`retry.py`, line 80):
```python
breaker = CircuitBreaker(
    failure_threshold=10,   # Open after 10 failures
    recovery_timeout=120,   # Try recovery after 2 minutes
    success_threshold=3     # Need 3 successes to close
)
```

### 3. Caching Strategy
**Cache Configuration** (`llm_integration_starter/cache.py`, line 15):
```python
cache = LRUCache(
    max_size=1000,    # Store 1000 responses
    ttl_seconds=7200  # 2-hour TTL
)
```

**Custom Cache Keys** (`cache.py`, line 60):
```python
def custom_cache_key(messages, provider, model):
    # Only cache by last user message
    last_msg = messages[-1]["content"]
    return f"{provider}:{model}:{last_msg[:100]}"
```

### 4. Cost Tracking
**Custom Pricing** (`llm_integration_starter/cost_tracker.py`, line 30):
```python
PRICING = {
    "claude": {
        "input": 3.00 / 1_000_000,   # $3 per 1M input tokens
        "output": 15.00 / 1_000_000  # $15 per 1M output tokens
    },
    "openai": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000
    },
    "custom": {
        "input": 5.00 / 1_000_000,
        "output": 20.00 / 1_000_000
    }
}
```

**Cost Alerts** (`cost_tracker.py`, line 120):
```python
tracker = CostTracker()
tracker.track(response)

if tracker.get_total_cost() > 100.0:  # $100 threshold
    send_alert("Cost threshold exceeded!")
```

### 5. Function Calling
**Custom Tool Definition** (`llm_integration_starter/function_calling.py`, line 50):
```python
from llm_integration_starter.function_calling import ToolDefinition

weather_tool = ToolDefinition(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g., 'San Francisco'"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature units"
            }
        },
        "required": ["location"]
    }
)
```

**Tool Execution** (`function_calling.py`, line 150):
```python
response = client.complete(messages, tools=[weather_tool])

if response.tool_calls:
    for call in response.tool_calls:
        if call.name == "get_weather":
            result = get_weather(**call.arguments)
            # Send result back to LLM
            messages.append({
                "role": "tool",
                "name": "get_weather",
                "content": json.dumps(result)
            })
```

## Advanced Features

### Streaming Responses
**Enable Streaming** (`llm_integration_starter/streaming.py`):
```python
from llm_integration_starter.client import UnifiedLLMClient

client = UnifiedLLMClient(provider="claude")

for chunk in client.stream(messages):
    print(chunk.delta, end="", flush=True)
print()  # Newline at end
```

**Custom Stream Handler** (`streaming.py`, line 80):
```python
def process_stream(stream):
    full_text = []
    for chunk in stream:
        full_text.append(chunk.delta)
        if len(full_text) % 10 == 0:  # Progress update every 10 chunks
            print(f"Received {len(full_text)} chunks...")
    return "".join(full_text)
```

### Fallback Chains
**Provider Redundancy** (`llm_integration_starter/fallback.py`):
```python
from llm_integration_starter.fallback import FallbackChain

chain = FallbackChain(providers=["claude", "openai", "gemini"])
result = chain.complete(messages)

if result.success:
    print(f"Success via {result.provider_used}")
else:
    print(f"All providers failed: {result.errors}")
```

### Batch Processing
**Parallel Requests** (add to `client.py`):
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def batch_complete(client, message_list, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(client.complete, msgs)
            for msgs in message_list
        ]
        return [f.result() for f in futures]

# Usage
messages_batch = [
    [{"role": "user", "content": "What is AI?"}],
    [{"role": "user", "content": "What is ML?"}],
]
results = batch_complete(client, messages_batch)
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

# Copy environment file
COPY .env .env

CMD ["llm-starter", "chat", "Hello"]
```

```bash
docker build -t llm-starter .
docker run --env-file .env llm-starter
```

### FastAPI Wrapper
```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_integration_starter import UnifiedLLMClient

app = FastAPI()
client = UnifiedLLMClient()

class CompletionRequest(BaseModel):
    messages: list[dict]
    provider: str = "mock"
    temperature: float = 0.7

@app.post("/complete")
def complete(req: CompletionRequest):
    try:
        response = client.complete(
            req.messages,
            provider=req.provider,
            temperature=req.temperature
        )
        return response.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```bash
pip install fastapi uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Common Errors

**Authentication Error: Invalid API Key**
- Verify key in `.env` file
- Check key is active at provider console
- Ensure no extra spaces: `ANTHROPIC_API_KEY=sk-ant-xxx` (no quotes)

**RateLimitError**
- Increase retry delays: `RetryPolicy(initial_delay=5.0)`
- Enable circuit breaker: `CircuitBreaker(failure_threshold=3)`
- Use fallback chain: `FallbackChain(providers=[...])`

**Streaming Returns Empty Chunks**
- Some providers send empty deltas at start/end
- Filter: `if chunk.delta: print(chunk.delta)`

**Function Calling Not Triggered**
- Verify tool definition matches provider format
- Check `FunctionCallingFormatter.format_tools()` output
- Some models require explicit instruction to use tools

### Debug Mode
**Enable Logging** (`client.py`, line 1):
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
```

**Inspect Requests** (httpx logging):
```bash
export HTTPX_LOG_LEVEL=debug
llm-starter chat "test" --provider claude
```

**Cost Analysis** (CLI):
```bash
# Add to cli.py
llm-starter stats --provider claude --last-24h
```

## Support Resources

- **GitHub Issues**: [llm-integration-starter/issues](https://github.com/ChunkyTortoise/llm-integration-starter/issues)
- **Documentation**: Module docstrings in `llm_integration_starter/` directory
- **Portfolio**: [chunkytortoise.github.io](https://chunkytortoise.github.io)
- **Related Projects**: [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) for production use
