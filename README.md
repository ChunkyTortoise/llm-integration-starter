[![Sponsor](https://img.shields.io/badge/Sponsor-💖-pink.svg)](https://github.com/sponsors/ChunkyTortoise)

# AI Agent Starter Kit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ct-llm-starter.streamlit.app)
[![CI](https://github.com/ChunkyTortoise/llm-integration-starter/workflows/CI/badge.svg)](https://github.com/ChunkyTortoise/llm-integration-starter/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-240%2B%20passing-brightgreen.svg)]()

**Production-ready agent templates for customer support, data analysis, content generation, and custom workflows -- powered by a unified multi-provider LLM interface.**

Build AI agents that work across Claude, OpenAI, and Gemini with built-in resilience patterns, MCP server templates, and tool use abstractions. Ships with 240+ tests and zero framework lock-in.

## What This Solves

- **Agent boilerplate** -- Pre-built templates for support, analysis, and content agents you can customize in minutes
- **Provider sprawl** -- One consistent client across Claude, OpenAI, and Gemini
- **MCP complexity** -- Starter server templates so you can build MCP tools without reading the entire spec
- **Missing production patterns** -- Retries, circuit breakers, caching, and cost tracking included

## Key Metrics

| Metric | Value |
|--------|-------|
| Tests | **240+ passing** |
| Agent Templates | 3 (Customer Support, Data Analyst, Content Generator) |
| MCP Templates | 2 (Basic Server, Multi-Tool Server) |
| LLM Providers | 4 (Claude, OpenAI, Gemini, Mock) |
| Circuit Breaker | Configurable half-open probes, auto-reset |
| Cache | LRU with TTL, hit-rate tracking |
| Core Dependencies | 3 (httpx, click, pydantic) |

## Demo

Live demo: https://ct-llm-starter.streamlit.app

## Quick Start

### Installation

```bash
git clone https://github.com/ChunkyTortoise/llm-integration-starter.git
cd llm-integration-starter

# Install core
pip install -e .

# Install with agent extras (LangGraph, MCP SDK)
pip install -e ".[agents]"

# Install dev dependencies
pip install -r requirements-dev.txt

cp .env.example .env
# Edit .env with your API keys
```

### Build a Customer Support Agent

```python
from llm_integration_starter import CustomerSupportAgent, UnifiedLLMClient

client = UnifiedLLMClient(provider="mock")  # swap to "claude" or "openai"

agent = CustomerSupportAgent(
    client=client,
    knowledge_base={
        "Password Reset": "Go to Settings > Security > Reset Password",
        "Billing": "Contact billing@example.com or visit /account/billing",
    },
)

result = agent.run("How do I reset my password?")
print(result.output)
```

### Analyze Data with an Agent

```python
from llm_integration_starter import DataAnalystAgent, UnifiedLLMClient

agent = DataAnalystAgent(client=UnifiedLLMClient(provider="mock"))

result = agent.run(
    "What's the average score?",
    data=[
        {"student": "Alice", "score": "95"},
        {"student": "Bob", "score": "87"},
        {"student": "Carol", "score": "92"},
    ],
)
print(result.output)
print(f"Rows analyzed: {result.metadata['rows_analyzed']}")
```

### Generate Content

```python
from llm_integration_starter import ContentGeneratorAgent, UnifiedLLMClient

agent = ContentGeneratorAgent(client=UnifiedLLMClient(provider="mock"))

# Blog post
result = agent.run("AI in healthcare", content_format="blog", tone="professional")

# Social media post
result = agent.run("New product launch", content_format="social")

# Email draft
result = agent.run("Follow-up meeting notes", content_format="email")
```

### Build an MCP Server

```python
from llm_integration_starter.mcp_templates.basic_server import BasicMCPServer, ToolSchema

server = BasicMCPServer(name="my-server")

server.register_tool(
    ToolSchema(
        name="lookup",
        description="Look up a customer by ID",
        input_schema={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    ),
    handler=lambda args: f"Customer {args['customer_id']} found",
)

# Handle JSON-RPC requests
response = server.handle_request({"method": "tools/list", "id": 1})
```

### Use the LLM Client Directly

```python
from llm_integration_starter import UnifiedLLMClient

client = UnifiedLLMClient(provider="mock")
messages = [{"role": "user", "content": "What is 2+2?"}]
response = client.complete(messages)

print(f"Response: {response.text}")
print(f"Cost: ${response.cost:.4f}")
print(f"Latency: {response.latency_ms:.0f}ms")
```

### CLI

```bash
llm-starter chat "Hello, world!"
llm-starter compare --providers claude,openai "Explain AI agents"
llm-starter benchmark --provider mock --n-requests 100
llm-starter fallback --providers claude,openai,gemini "Hello"
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Agent Templates                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Customer     │  │  Data        │  │  Content     │       │
│  │  Support      │  │  Analyst     │  │  Generator   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                   UnifiedLLMClient                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Cache   │  │  Retry   │  │ Fallback │  │   Cost   │     │
│  │  Layer   │  │  Logic   │  │  Chain   │  │ Tracker  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└────────────────────────────┬──────────────────────────────────┘
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼─────────┐ ┌─────▼──────┐ ┌─────────▼────────┐
│ Claude Provider   │ │ OpenAI     │ │ Gemini Provider  │
└───────────────────┘ └────────────┘ └──────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    MCP Server Templates                        │
│  ┌──────────────────┐  ┌──────────────────────┐              │
│  │  Basic Server    │  │  Multi-Tool Server   │              │
│  │  (1 tool)        │  │  (3 tools)           │              │
│  └──────────────────┘  └──────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
```

## Module Guide

### Agent Templates (`agents/`)

| Module | Description |
|--------|-------------|
| `base.py` | `BaseAgent` abstract class -- common interface with `run()`, `tools`, `system_prompt` |
| `customer_support.py` | Support agent with knowledge base search and empathetic responses |
| `data_analyst.py` | Data agent that loads CSV files, summarizes data, generates insights |
| `content_generator.py` | Content agent for blog, social, and email formats |
| `langgraph_agent.py` | Stateful ReAct agent built on LangGraph `StateGraph` (requires `[agents]` extra) |

#### LangGraph ReAct Agent

Build stateful agents with tool use using LangGraph's `StateGraph`:

```python
from llm_integration_starter.agents.langgraph_agent import LangGraphReActAgent

def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b

agent = LangGraphReActAgent(tools={"add": add})
result = agent.run("What is 42 + 58?")
print(result.output)       # LLM's final answer
print(result.metadata)     # {"iterations": 1, "tools_used": ["add"], ...}
```

The graph follows a reason → act → END loop: the LLM reasons and emits tool calls, tools execute and feed results back, then the LLM produces a final answer. Install with:

```bash
pip install "ai-agent-starter-kit[agents]"
```

Gracefully falls back to a single-shot LLM call when LangGraph is not installed.

### MCP Templates (`mcp_templates/`)

| Module | Description |
|--------|-------------|
| `basic_server.py` | Minimal MCP server -- one tool, JSON-RPC routing, stdin/stdout |
| `multi_tool_server.py` | Multi-tool server with echo, word_count, and reverse_text examples |

### LLM Integration (existing)

| Module | Description |
|--------|-------------|
| `client.py` | Unified interface for all providers |
| `providers/` | Claude, OpenAI, Gemini, and Mock implementations |
| `function_calling.py` | Cross-provider tool use abstraction |
| `streaming.py` | SSE parser for real-time responses |
| `retry.py` | Exponential backoff + circuit breaker |
| `fallback.py` | Provider chain failover |
| `cache.py` | LRU cache with TTL |
| `cost_tracker.py` | Per-provider cost monitoring |
| `guardrails.py` | Content filtering, PII detection, prompt injection defense |
| `cli.py` | Command-line interface |

## Service Mapping

- Service 4: Multi-Agent Workflows (Agentic AI Systems)
- Service 5: Prompt Engineering and System Optimization
- Service 6: AI-Powered Personal and Business Automation

## Certification Mapping

- IBM RAG and Agentic AI Professional Certificate
- IBM Generative AI Engineering with PyTorch, LangChain & Hugging Face
- Duke University LLMOps Specialization
- Vanderbilt Generative AI Strategic Leader Specialization
- Google Cloud Generative AI Leader Certificate

## Test Coverage

**275+ tests across 12+ test files:**

| Module | Tests | Coverage |
|--------|-------|----------|
| `agents/` | 46 | Agent templates + base class + LangGraph ReAct agent |
| `mcp_templates/` | 9 | MCP server templates |
| `client.py` | 12 | Core functionality |
| `providers/` | 12 | Mock provider + base class |
| `streaming.py` | 12 | SSE parsing |
| `function_calling.py` | 12 | Tool formatting & parsing |
| `retry.py` | 10 | Retry logic + circuit breaker |
| `fallback.py` | 8 | Fallback chain logic |
| `cache.py` | 12 | LRU cache + TTL |
| `cost_tracker.py` | 11 | Cost tracking & analytics |
| `cli.py` | 7 | CLI commands |

```bash
make test
python -m pytest tests/ -v --cov=llm_integration_starter --cov-report=html
```

## Architecture Decisions

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](docs/adr/0001-circuit-breaker-pattern.md) | Circuit Breaker Pattern | Accepted |
| [ADR-0002](docs/adr/0002-fallback-chain-design.md) | Fallback Chain Design | Accepted |
| [ADR-0003](docs/adr/0003-response-caching-strategy.md) | Response Caching Strategy | Accepted |

## Learning Path

1. **Start with `agents/base.py`**: Understand the agent interface
2. **Try `agents/customer_support.py`**: See how agents wrap the LLM client
3. **Build with `mcp_templates/basic_server.py`**: Create your first MCP server
4. **Study `providers/mock.py`**: Understand the provider interface
5. **Read `client.py`**: Learn the unified client pattern
6. **Explore `function_calling.py`**: Learn tool use abstraction
7. **Review `retry.py` & `fallback.py`**: Learn resilience patterns
8. **Try the `cli.py`**: Interactive experimentation

## When to Use This vs Other Tools

| Feature | AI Agent Starter Kit | LangChain | CrewAI |
|---------|---------------------|-----------|--------|
| **Purpose** | Learn + build agents | Full framework | Multi-agent teams |
| **Complexity** | Low (focused modules) | High (100+ modules) | Medium |
| **Dependencies** | 3 core | 20+ | 10+ |
| **Agent Templates** | 3 ready-to-use | Build from scratch | Role-based |
| **MCP Support** | Templates included | Via plugins | No |
| **Best For** | Learning patterns, fast prototypes | Full-featured apps | Team orchestration |

## Related Projects

- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) -- AgentForge: unified async LLM interface
- [EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) -- Real estate AI platform with BI dashboards
- [prompt-engineering-lab](https://github.com/ChunkyTortoise/prompt-engineering-lab) -- 8 prompt patterns, A/B testing
- [Portfolio](https://chunkytortoise.github.io) -- Project showcase and services

## Development

```bash
make install    # Install in dev mode
make format     # Format code
make lint       # Lint code
make test       # Run tests
make clean      # Clean build artifacts
```

## Contributing

Contributions welcome! Prioritize clarity over cleverness, add detailed comments, and include tests.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**ChunkyTortoise**
- GitHub: [@ChunkyTortoise](https://github.com/ChunkyTortoise)
- Portfolio: [chunkytortoise.github.io](https://chunkytortoise.github.io)
