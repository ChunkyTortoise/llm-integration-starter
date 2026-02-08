# LLM Integration Starter

[![CI](https://github.com/chunkytortoise/llm-integration-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/chunkytortoise/llm-integration-starter/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Production-ready LLM integration patterns: completion, streaming, function calling, RAG, and hardening. Each module is a self-contained recipe for adding AI capabilities to any application -- no API keys required for development and testing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Demo (app.py)                   │
│   ┌──────────┬──────────┬──────────┬──────┬──────────────┐  │
│   │Completion│Streaming │Func Call │ RAG  │  Dashboard   │  │
│   └────┬─────┴────┬─────┴────┬─────┴──┬───┴──────┬───────┘  │
├────────┼──────────┼──────────┼────────┼──────────┼──────────┤
│        │          │          │        │          │           │
│  ┌─────▼───┐ ┌────▼────┐ ┌──▼──┐ ┌──▼──┐ ┌─────▼──────┐   │
│  │Complete │ │Streaming│ │Func │ │ RAG │ │ Cost +     │   │
│  │ Client  │ │ Client  │ │Call │ │Pipe │ │ Latency    │   │
│  └─────┬───┘ └────┬────┘ └──┬──┘ └──┬──┘ │ Trackers   │   │
│        │          │         │       │    └────────────┘   │
│  ┌─────▼──────────▼─────────▼───────▼──────────────────┐   │
│  │              MockLLM (mock_llm.py)                   │   │
│  │   Deterministic responses, no API keys needed        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Hardening (hardening.py)                   │   │
│  │   Circuit Breaker + Retry + Rate Limiting             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Modules

| Module | File | Description |
|--------|------|-------------|
| **Mock LLM** | `mock_llm.py` | Deterministic LLM mock with canned responses, streaming, and function calling |
| **Completion** | `completion.py` | Basic completion client with system prompts and FastAPI endpoint factory |
| **Streaming** | `streaming.py` | SSE streaming with chunk-by-chunk event generation |
| **Function Calling** | `function_calling.py` | Tool registration, LLM-driven tool selection, and execution pipeline |
| **RAG Pipeline** | `rag_pipeline.py` | TF-IDF vectorization, cosine similarity retrieval, context-augmented generation |
| **Hardening** | `hardening.py` | Circuit breaker (closed/open/half-open), retry with backoff, timeout |
| **Cost Tracker** | `cost_tracker.py` | Per-request cost recording, daily/monthly projections, model-level breakdown |
| **Latency Tracker** | `latency_tracker.py` | P50/P95/P99 percentiles with rolling window cleanup |

## Quick Start

```bash
# Clone and install
git clone https://github.com/chunkytortoise/llm-integration-starter.git
cd llm-integration-starter
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Launch demo
streamlit run app.py

# Lint
ruff check . && ruff format --check .
```

Or use the Makefile:

```bash
make setup    # Install dependencies
make test     # Run tests
make lint     # Check code quality
make demo     # Launch Streamlit app
```

## Key Features

### Mock LLM (Zero-Config Development)
- Deterministic responses for reproducible testing
- Canned response matching by keyword
- Simulated latency, token counting, and call logging
- Drop-in replacement for real LLM clients

### Completion Client
- System prompt support
- Context augmentation for RAG-style queries
- FastAPI endpoint factory for instant API creation
- Full token usage tracking

### SSE Streaming
- Server-Sent Events format for real-time UI updates
- Chunk-by-chunk delivery with event IDs
- Done event with total chunk count
- FastAPI streaming endpoint factory

### Function Calling
- Tool definition with JSON Schema parameters
- 3 built-in demo tools: calculate, lookup, format_data
- Custom tool registration
- Full pipeline: LLM call -> tool selection -> execution -> result

### RAG Pipeline
- TF-IDF vectorization with scikit-learn
- Cosine similarity retrieval
- Configurable top-K
- Source attribution with relevance scores

### Production Hardening
- Circuit breaker: closed -> open -> half-open state machine
- Configurable failure threshold and recovery timeout
- Automatic retry with attempt tracking
- Request statistics and health monitoring

### Observability
- **Cost tracking**: Per-request pricing, model-level breakdown, daily/monthly projections
- **Latency tracking**: P50/P95/P99 percentiles with configurable rolling window

## Project Structure

```
llm-integration-starter/
├── llm_starter/
│   ├── __init__.py
│   ├── mock_llm.py          # Mock LLM foundation
│   ├── completion.py         # Basic completion pattern
│   ├── streaming.py          # SSE streaming
│   ├── function_calling.py   # Tool definitions + execution
│   ├── rag_pipeline.py       # TF-IDF RAG pipeline
│   ├── hardening.py          # Circuit breaker + retry
│   ├── cost_tracker.py       # Cost tracking + projections
│   └── latency_tracker.py    # P50/P95/P99 latency
├── tests/                     # 76+ tests across 7 files
├── demo_data/                 # Sample documents for RAG
├── app.py                     # Streamlit demo (5 tabs)
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Makefile
└── .github/workflows/ci.yml
```

## License

MIT License. See [LICENSE](LICENSE) for details.
