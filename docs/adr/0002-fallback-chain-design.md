# ADR 0002: Fallback Chain Design

## Status
Accepted

## Context
Relying on a single LLM provider creates a single point of failure. When the primary provider experiences an outage or degradation, the entire application stops functioning. We need resilience through provider redundancy with transparent failover.

## Decision
Implement a configurable fallback chain (e.g., Claude -> GPT-4 -> local model). Each provider in the chain maintains a health score based on recent success rate and latency. When the primary provider fails or its circuit breaker opens, the request automatically routes to the next healthy provider in the chain. Health scores recover over time as providers stabilize.

## Consequences
- **Positive**: Achieves 99.9% effective uptime through provider redundancy. Failover is transparent to the calling code. Health scores enable intelligent routing that prefers the best-performing available provider.
- **Negative**: Fallback providers may differ in response quality, capability, and cost. The application must handle response format differences across providers. Maintaining API keys and configurations for multiple providers increases operational overhead.
