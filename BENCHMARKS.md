# LLM Integration Starter -- Benchmarks

Generated: 2026-02-08

## Test Suite Summary

88 tests across 8 modules. All tests run with MockLLM (no API keys required).

| Module | Test File | Tests | Description |
|--------|-----------|-------|-------------|
| Mock LLM | `test_mock_llm.py` | ~12 | Deterministic responses, streaming, function calling |
| Completion | `test_completion.py` | ~11 | System prompts, context augmentation, endpoint factory |
| Streaming | `test_streaming.py` | ~11 | SSE events, chunk delivery, done signal |
| Function Calling | `test_function_calling.py` | ~11 | Tool registration, selection, execution pipeline |
| RAG Pipeline | `test_rag_pipeline.py` | ~11 | TF-IDF indexing, retrieval, source attribution |
| Hardening | `test_hardening.py` | ~12 | Circuit breaker states, retry backoff, timeout |
| Cost Tracker | `test_cost_tracker.py` | ~10 | Per-request cost, projections, model breakdown |
| Latency Tracker | `test_latency_tracker.py` | ~10 | P50/P95/P99, rolling window, cleanup |
| **Total** | **8 files** | **88** | |

## How to Reproduce

```bash
git clone https://github.com/ChunkyTortoise/llm-integration-starter.git
cd llm-integration-starter
pip install -r requirements-dev.txt
make test
# or: python -m pytest tests/ -v
```

## Notes

- All tests use MockLLM for deterministic, reproducible results
- No external API calls or network access required
- Circuit breaker tests use simulated time progression
- Cost tracker tests use known pricing rates for verification
