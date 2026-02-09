# ADR 0001: Circuit Breaker Pattern

## Status
Accepted

## Context
LLM APIs exhibit variable latency and occasional outages. Without protection, a failing upstream API causes cascading failures: threads block waiting for timeouts, retry storms amplify load, and the entire application degrades. We need a mechanism to detect failures quickly and fail fast rather than waiting for inevitable timeouts.

## Decision
Implement a three-state circuit breaker: closed (normal operation), open (fast-fail, no requests sent), and half-open (probe with limited requests to test recovery). The failure threshold and recovery timeout are configurable per provider. State transitions are logged for observability.

## Consequences
- **Positive**: Prevents cascade failures by isolating unhealthy providers. Fast-fail behavior (returning immediately rather than waiting for timeout) preserves application responsiveness. Half-open state enables automatic recovery detection without manual intervention.
- **Negative**: Adds approximately 1ms overhead per request for state checking. Requires threshold tuning per provider since failure patterns differ. During open state, all requests to that provider fail immediately, which may be too aggressive if only a subset of the API is degraded.
