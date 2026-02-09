# ADR 0003: Response Caching Strategy

## Status
Accepted

## Context
Many LLM use cases involve identical or near-identical prompts generating similar responses. Each uncached call incurs API cost and latency. For deterministic queries (e.g., classification, extraction, formatting), caching can eliminate redundant API calls entirely.

## Decision
Implement content-hash caching where the prompt (and relevant parameters like temperature and model) are hashed to produce a cache key. Cached responses have a configurable TTL (time-to-live). An optional semantic similarity layer can match near-identical prompts to cached responses using embedding distance thresholds.

## Consequences
- **Positive**: Achieves 60-80% cache hit rate for typical workloads. Cached responses have zero API cost and near-zero latency. Semantic matching extends cache utility to paraphrased but equivalent queries.
- **Negative**: Stale cache is problematic for time-sensitive queries (mitigated by TTL). Cache invalidation adds complexity, especially for semantic matching where "similar enough" is subjective. Cache storage grows with prompt diversity and requires periodic eviction.
