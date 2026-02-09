# LLM Integration Starter Benchmark Results

**Date**: 2026-02-09 03:35:39

| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|-----------|-----------|----------|----------|----------|------------|
| LRU Cache Ops (200 write, 300 read, 200 evict) | 500 | 0.0608 | 0.1198 | 0.1678 | 14,801 ops/sec |
| Circuit Breaker (500 events, 5 providers) | 1,000 | 0.0517 | 0.0842 | 0.1232 | 18,047 ops/sec |
| Fallback Chain Traversal (100 chains) | 1,000 | 0.0358 | 0.0408 | 0.0702 | 27,052 ops/sec |
| Batch Queue (500 items, batch=32) | 500 | 0.1661 | 0.2456 | 0.4245 | 5,574 ops/sec |

> All benchmarks use synthetic data. No external services required.
