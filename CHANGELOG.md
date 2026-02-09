# Changelog

All notable changes to llm-integration-starter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Safety & guardrails engine — injection detection, PII redaction, content filtering (+33 tests)
- Observability collector and batch processor (+71 tests)

## [1.0.0] - 2026-02-08

### Added
- Mock LLM provider for testing without API keys
- Circuit breaker with three-state (closed/open/half-open) pattern
- Fallback chain with configurable provider priority
- Response caching with content-hash keys and TTL
- Streaming response handler
- 220+ automated tests
- GitHub Actions CI with Codecov integration
