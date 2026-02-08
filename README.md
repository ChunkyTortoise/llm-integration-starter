# LLM Integration Starter

**Production-ready LLM integration patterns: completion, streaming, function calling, RAG, and hardening.** Each module is a self-contained recipe for adding AI capabilities to any application -- no API keys required for development and testing.

![CI](https://github.com/ChunkyTortoise/llm-integration-starter/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![Tests](https://img.shields.io/badge/tests-88%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## What This Solves

- **No starting point for LLM integration** -- 8 self-contained modules covering every common pattern from basic completion to production hardening
- **API keys block local development** -- MockLLM provides deterministic responses with simulated latency and token counting
- **Production reliability is an afterthought** -- Circuit breaker, retry with backoff, and rate limiting built in from day one
- **Cost visibility comes too late** -- Per-request cost tracking with daily/monthly projections and model-level breakdown

## Architecture

```
+-------------------------------------------------------------+
|                    Streamlit Demo (app.py)                    |
|   +----------+----------+----------+------+--------------+   |
|   |Completion|Streaming |Func Call | RAG  |  Dashboard   |   |
|   +----+-----+----+-----+----+-----+--+---+------+-------+   |
+--------+----------+----------+--------+----------+-----------+
         |          |          |        |          |
   +-----v---+ +---v----+ +--v--+ +--v--+ +-----v------+
   |Complete | |Stream  | |Func | | RAG | | Cost +     |
   | Client  | | Client | |Call | |Pipe | | Latency    |
   +-----+---+ +---+----+ +--+--+ +--+--+ | Trackers   |
         |         |          |       |    +------------+
   +-----v---------v----------v-------v----------------+
   |              MockLLM (mock_llm.py)                 |
   |   Deterministic responses, no API keys needed      |
   +----------------------------------------------------+
   |            Hardening (hardening.py)                 |
   |   Circuit Breaker + Retry + Rate Limiting           |
   +----------------------------------------------------+
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
git clone https://github.com/ChunkyTortoise/llm-integration-starter.git
cd llm-integration-starter
pip install -r requirements-dev.txt
make test
make demo
```

## Key Features

### Mock LLM (Zero-Config Development)
- Deterministic responses for reproducible testing
- Canned response matching by keyword
- Simulated latency, token counting, and call logging

### Completion Client
- System prompt support and context augmentation
- FastAPI endpoint factory for instant API creation

### SSE Streaming
- Server-Sent Events format for real-time UI updates
- Chunk-by-chunk delivery with event IDs

### Function Calling
- Tool definition with JSON Schema parameters
- 3 built-in demo tools: calculate, lookup, format_data

### RAG Pipeline
- TF-IDF vectorization with cosine similarity retrieval
- Configurable top-K with source attribution

### Production Hardening
- Circuit breaker: closed -> open -> half-open state machine
- Automatic retry with configurable backoff

### Observability
- **Cost tracking**: Per-request pricing, model-level breakdown, daily/monthly projections
- **Latency tracking**: P50/P95/P99 percentiles with configurable rolling window

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit (5 tabs) |
| ML | scikit-learn (TF-IDF) |
| API | FastAPI (endpoint factories) |
| Testing | pytest (88 tests) |
| CI | GitHub Actions (Python 3.11, 3.12) |
| Linting | Ruff |

## Project Structure

```
llm-integration-starter/
├── app.py                          # Streamlit demo (5 tabs)
├── llm_starter/
│   ├── mock_llm.py                 # Mock LLM foundation
│   ├── completion.py               # Basic completion pattern
│   ├── streaming.py                # SSE streaming
│   ├── function_calling.py         # Tool definitions + execution
│   ├── rag_pipeline.py             # TF-IDF RAG pipeline
│   ├── hardening.py                # Circuit breaker + retry
│   ├── cost_tracker.py             # Cost tracking + projections
│   └── latency_tracker.py          # P50/P95/P99 latency
├── demo_data/                      # Sample documents for RAG
├── tests/                          # 8 test files, one per module
├── .github/workflows/ci.yml        # CI pipeline
├── Makefile                        # demo, test, lint, setup
└── requirements-dev.txt
```

## Testing

```bash
make test                           # Full suite (88 tests)
python -m pytest tests/ -v          # Verbose output
python -m pytest tests/test_hardening.py  # Single module
```

## Related Projects

- [EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) -- Real estate AI platform with BI dashboards and CRM integration
- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) -- AgentForge: unified async LLM interface (Claude, Gemini, OpenAI, Perplexity)
- [docqa-engine](https://github.com/ChunkyTortoise/docqa-engine) -- RAG document Q&A with hybrid retrieval and prompt engineering lab
- [insight-engine](https://github.com/ChunkyTortoise/insight-engine) -- Upload CSV/Excel, get instant dashboards, predictive models, and reports
- [scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve) -- Web scraping, price monitoring, Excel-to-web apps, and SEO tools
- [prompt-engineering-lab](https://github.com/ChunkyTortoise/prompt-engineering-lab) -- 8 prompt patterns, A/B testing, TF-IDF evaluation
- [Portfolio](https://chunkytortoise.github.io) -- Project showcase and services

## License

MIT License. See [LICENSE](LICENSE) for details.
