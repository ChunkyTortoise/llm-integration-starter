"""Batch processor for LLM requests with retry support."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BatchItem:
    """A single item in a batch."""

    id: str
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchItemResult:
    """Result of processing a single batch item."""

    id: str
    response: str
    latency_ms: float
    success: bool
    error: str | None = None


@dataclass
class BatchReport:
    """Summary report of a batch processing run."""

    results: list[BatchItemResult]
    total: int
    succeeded: int
    failed: int
    total_latency_ms: float
    avg_latency_ms: float


def _default_process(item: BatchItem) -> str:
    """Default processing function: echo the prompt."""
    return f"Processed: {item.prompt}"


class BatchProcessor:
    """Processes batches of LLM requests with retry logic."""

    def __init__(
        self,
        process_fn: Callable[[BatchItem], str] | None = None,
        max_retries: int = 2,
    ) -> None:
        self._process_fn = process_fn or _default_process
        self._max_retries = max_retries

    def process(self, items: list[BatchItem]) -> BatchReport:
        """Process a batch of items and return a report."""
        results: list[BatchItemResult] = []
        for item in items:
            result = self._process_single(item)
            results.append(result)

        # Retry failed items
        failed_items = [items[i] for i, r in enumerate(results) if not r.success]
        if failed_items:
            retry_results = self._retry_failed(failed_items)
            # Update results with retry outcomes
            retry_map = {r.id: r for r in retry_results}
            for i, r in enumerate(results):
                if not r.success and r.id in retry_map:
                    results[i] = retry_map[r.id]

        total_latency = sum(r.latency_ms for r in results)
        succeeded = sum(1 for r in results if r.success)

        return BatchReport(
            results=results,
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            total_latency_ms=round(total_latency, 2),
            avg_latency_ms=round(total_latency / len(results), 2) if results else 0.0,
        )

    def process_with_progress(self, items: list[BatchItem]) -> Iterator[tuple[int, BatchItemResult]]:
        """Process items yielding (index, result) pairs for progress tracking."""
        for i, item in enumerate(items):
            result = self._process_single(item)
            yield i, result

    def _process_single(self, item: BatchItem) -> BatchItemResult:
        """Process a single item with timing."""
        start = time.monotonic()
        try:
            response = self._process_fn(item)
            elapsed = (time.monotonic() - start) * 1000
            return BatchItemResult(
                id=item.id,
                response=response,
                latency_ms=round(elapsed, 2),
                success=True,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return BatchItemResult(
                id=item.id,
                response="",
                latency_ms=round(elapsed, 2),
                success=False,
                error=str(e),
            )

    def _retry_failed(self, failed: list[BatchItem]) -> list[BatchItemResult]:
        """Retry failed items up to max_retries times."""
        results: list[BatchItemResult] = []
        for item in failed:
            result = None
            for _ in range(self._max_retries):
                result = self._process_single(item)
                if result.success:
                    break
            if result is not None:
                results.append(result)
        return results
