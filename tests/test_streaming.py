"""Tests for StreamingClient and SSE events."""

from __future__ import annotations

import json

from llm_starter.mock_llm import MockLLM
from llm_starter.streaming import StreamEvent, StreamingClient, format_sse_event


class TestStreamEvent:
    """Tests for StreamEvent formatting."""

    def test_format_sse(self) -> None:
        event = StreamEvent(event="message", data="hello")
        sse = event.format_sse()
        assert "event: message" in sse
        assert "data: hello" in sse

    def test_format_with_id(self) -> None:
        event = StreamEvent(event="message", data="hello", id="42")
        sse = event.format_sse()
        assert "id: 42" in sse

    def test_message_event(self) -> None:
        event = StreamEvent(event="message", data='{"chunk": "hi"}')
        sse = event.format_sse()
        assert "event: message" in sse
        assert '{"chunk": "hi"}' in sse

    def test_done_event(self) -> None:
        event = StreamEvent(event="done", data='{"total": 5}')
        sse = event.format_sse()
        assert "event: done" in sse


class TestStreamingClient:
    """Tests for StreamingClient."""

    def test_stream_completion(self) -> None:
        llm = MockLLM(default_response="one two three")
        client = StreamingClient(llm)
        events = client.stream_completion("test")
        # 3 message events + 1 done event
        assert len(events) == 4

    def test_last_event_is_done(self) -> None:
        llm = MockLLM(default_response="word")
        client = StreamingClient(llm)
        events = client.stream_completion("test")
        assert events[-1].event == "done"

    def test_stream_to_string(self) -> None:
        llm = MockLLM(default_response="hello world test")
        client = StreamingClient(llm)
        result = client.stream_to_string("test")
        assert result == "hello world test"

    def test_stream_event_count(self) -> None:
        llm = MockLLM(default_response="a b c d e")
        client = StreamingClient(llm)
        events = client.stream_completion("test")
        message_events = [e for e in events if e.event == "message"]
        assert len(message_events) == 5

    def test_stream_event_data_is_json(self) -> None:
        llm = MockLLM(default_response="hello")
        client = StreamingClient(llm)
        events = client.stream_completion("test")
        data = json.loads(events[0].data)
        assert "chunk" in data
        assert data["chunk"] == "hello"

    def test_done_event_has_total(self) -> None:
        llm = MockLLM(default_response="a b c")
        client = StreamingClient(llm)
        events = client.stream_completion("test")
        done_data = json.loads(events[-1].data)
        assert done_data["total_chunks"] == 3


class TestFormatSSE:
    """Tests for format_sse_event helper."""

    def test_format_function(self) -> None:
        result = format_sse_event("message", "data here")
        assert "event: message" in result
        assert "data: data here" in result

    def test_empty_data(self) -> None:
        result = format_sse_event("ping", "")
        assert "event: ping" in result
        assert "data: " in result
