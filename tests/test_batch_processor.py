"""Tests for batch processor."""

from __future__ import annotations

from llm_starter.batch_processor import (
    BatchItem,
    BatchItemResult,
    BatchProcessor,
    BatchReport,
)


def _make_item(prompt: str = "test prompt", item_id: str | None = None) -> BatchItem:
    return BatchItem(id=item_id or f"item-{id(prompt)}", prompt=prompt)


class TestBatchProcessor:
    def test_process_empty_batch(self) -> None:
        bp = BatchProcessor()
        report = bp.process([])
        assert isinstance(report, BatchReport)
        assert report.total == 0
        assert report.succeeded == 0
        assert report.failed == 0

    def test_process_single_item(self) -> None:
        bp = BatchProcessor()
        items = [_make_item("Hello")]
        report = bp.process(items)
        assert report.total == 1
        assert report.succeeded == 1
        assert report.failed == 0
        assert "Processed: Hello" in report.results[0].response

    def test_process_multiple_items(self) -> None:
        bp = BatchProcessor()
        items = [_make_item(f"Prompt {i}", item_id=f"i-{i}") for i in range(5)]
        report = bp.process(items)
        assert report.total == 5
        assert report.succeeded == 5

    def test_process_all_succeed(self) -> None:
        def ok_fn(item: BatchItem) -> str:
            return f"OK: {item.prompt}"

        bp = BatchProcessor(process_fn=ok_fn)
        items = [_make_item("test", item_id="a")]
        report = bp.process(items)
        assert report.succeeded == 1
        assert report.results[0].response == "OK: test"

    def test_process_with_failures_and_retry(self) -> None:
        call_count: dict[str, int] = {}

        def flaky_fn(item: BatchItem) -> str:
            call_count[item.id] = call_count.get(item.id, 0) + 1
            if call_count[item.id] <= 1:
                msg = "Temporary error"
                raise RuntimeError(msg)
            return "Recovered"

        bp = BatchProcessor(process_fn=flaky_fn, max_retries=2)
        items = [_make_item("flaky", item_id="flaky-1")]
        report = bp.process(items)
        assert report.succeeded == 1
        assert report.results[0].response == "Recovered"

    def test_process_permanent_failure(self) -> None:
        def fail_fn(item: BatchItem) -> str:
            msg = "Always fails"
            raise RuntimeError(msg)

        bp = BatchProcessor(process_fn=fail_fn, max_retries=2)
        items = [_make_item("fail", item_id="f-1")]
        report = bp.process(items)
        assert report.failed == 1
        assert report.results[0].success is False
        assert report.results[0].error is not None

    def test_report_stats_correct(self) -> None:
        def mixed_fn(item: BatchItem) -> str:
            if item.id == "bad":
                msg = "Fail"
                raise RuntimeError(msg)
            return "OK"

        bp = BatchProcessor(process_fn=mixed_fn, max_retries=1)
        items = [
            BatchItem(id="good1", prompt="a"),
            BatchItem(id="bad", prompt="b"),
            BatchItem(id="good2", prompt="c"),
        ]
        report = bp.process(items)
        assert report.total == 3
        assert report.succeeded == 2
        assert report.failed == 1
        assert report.total_latency_ms >= 0
        assert report.avg_latency_ms >= 0

    def test_custom_process_fn(self) -> None:
        def upper_fn(item: BatchItem) -> str:
            return item.prompt.upper()

        bp = BatchProcessor(process_fn=upper_fn)
        items = [_make_item("hello", item_id="u1")]
        report = bp.process(items)
        assert report.results[0].response == "HELLO"

    def test_process_with_progress(self) -> None:
        bp = BatchProcessor()
        items = [_make_item(f"item-{i}", item_id=f"p-{i}") for i in range(3)]
        progress = list(bp.process_with_progress(items))
        assert len(progress) == 3
        assert progress[0][0] == 0
        assert progress[1][0] == 1
        assert progress[2][0] == 2
        assert all(isinstance(r, BatchItemResult) for _, r in progress)

    def test_process_with_progress_single(self) -> None:
        bp = BatchProcessor()
        items = [_make_item("only", item_id="single")]
        progress = list(bp.process_with_progress(items))
        assert len(progress) == 1
        assert progress[0][1].success is True

    def test_retry_exhaustion(self) -> None:
        def always_fail(item: BatchItem) -> str:
            msg = "Nope"
            raise RuntimeError(msg)

        bp = BatchProcessor(process_fn=always_fail, max_retries=3)
        items = [_make_item("x", item_id="exhaust")]
        report = bp.process(items)
        assert report.failed == 1

    def test_latency_recorded(self) -> None:
        bp = BatchProcessor()
        items = [_make_item("timing", item_id="t1")]
        report = bp.process(items)
        assert report.results[0].latency_ms >= 0

    def test_default_process_fn(self) -> None:
        bp = BatchProcessor()
        items = [_make_item("echo me", item_id="d1")]
        report = bp.process(items)
        assert "echo me" in report.results[0].response

    def test_metadata_preserved(self) -> None:
        item = BatchItem(id="m1", prompt="test", metadata={"key": "value"})
        assert item.metadata == {"key": "value"}

    def test_batch_item_defaults(self) -> None:
        item = BatchItem(id="default", prompt="test")
        assert item.metadata == {}

    def test_mixed_success_and_failure(self) -> None:
        counter = {"calls": 0}

        def alternating(item: BatchItem) -> str:
            counter["calls"] += 1
            if item.id.endswith("fail"):
                msg = "Fail"
                raise RuntimeError(msg)
            return "OK"

        bp = BatchProcessor(process_fn=alternating, max_retries=1)
        items = [
            BatchItem(id="ok1", prompt="a"),
            BatchItem(id="will_fail", prompt="b"),
            BatchItem(id="ok2", prompt="c"),
        ]
        report = bp.process(items)
        assert report.succeeded == 2
        assert report.failed == 1

    def test_avg_latency_with_multiple(self) -> None:
        bp = BatchProcessor()
        items = [_make_item(f"i{i}", item_id=f"lat-{i}") for i in range(5)]
        report = bp.process(items)
        assert report.avg_latency_ms >= 0
        expected_avg = report.total_latency_ms / 5
        assert abs(report.avg_latency_ms - expected_avg) < 0.1

    def test_process_with_progress_empty(self) -> None:
        bp = BatchProcessor()
        progress = list(bp.process_with_progress([]))
        assert progress == []

    def test_zero_retries(self) -> None:
        def fail_fn(item: BatchItem) -> str:
            msg = "Fail"
            raise RuntimeError(msg)

        bp = BatchProcessor(process_fn=fail_fn, max_retries=0)
        items = [_make_item("x", item_id="no-retry")]
        report = bp.process(items)
        assert report.failed == 1
