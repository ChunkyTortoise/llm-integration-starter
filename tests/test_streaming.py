"""Tests for streaming response parser."""

from __future__ import annotations

from llm_integration_starter.streaming import StreamDelta, StreamingParser


class TestStreamDelta:
    """Tests for StreamDelta dataclass."""

    def test_stream_delta_creation(self):
        """Test creating a StreamDelta."""
        delta = StreamDelta(token="Hello", is_final=False, latency_ms=100.0)
        assert delta.token == "Hello"
        assert delta.is_final is False
        assert delta.latency_ms == 100.0


class TestStreamingParser:
    """Tests for StreamingParser."""

    def test_parser_initialization(self):
        """Test creating a parser."""
        parser = StreamingParser()
        assert parser is not None

    def test_parse_claude_content_delta(self):
        """Test parsing Claude content delta."""
        parser = StreamingParser()
        line = 'data: {"type": "content_block_delta", "delta": {"text": "Hello"}}'
        delta = parser.parse_sse_line(line, provider="claude")

        assert delta is not None
        assert delta.token == "Hello"
        assert delta.is_final is False

    def test_parse_claude_message_stop(self):
        """Test parsing Claude message stop event."""
        parser = StreamingParser()
        line = 'data: {"type": "message_stop"}'
        delta = parser.parse_sse_line(line, provider="claude")

        assert delta is not None
        assert delta.token == ""
        assert delta.is_final is True

    def test_parse_openai_delta(self):
        """Test parsing OpenAI delta."""
        parser = StreamingParser()
        line = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
        delta = parser.parse_sse_line(line, provider="openai")

        assert delta is not None
        assert delta.token == "Hello"
        assert delta.is_final is False

    def test_parse_openai_finish(self):
        """Test parsing OpenAI finish reason."""
        parser = StreamingParser()
        line = 'data: {"choices": [{"finish_reason": "stop"}]}'
        delta = parser.parse_sse_line(line, provider="openai")

        assert delta is not None
        assert delta.is_final is True

    def test_parse_done_marker(self):
        """Test parsing [DONE] marker."""
        parser = StreamingParser()
        line = "data: [DONE]"
        delta = parser.parse_sse_line(line, provider="openai")

        assert delta is not None
        assert delta.is_final is True

    def test_parse_invalid_line(self):
        """Test parsing invalid line returns None."""
        parser = StreamingParser()
        delta = parser.parse_sse_line("invalid line", provider="claude")
        assert delta is None

    def test_parse_non_data_line(self):
        """Test parsing non-data line returns None."""
        parser = StreamingParser()
        delta = parser.parse_sse_line("event: ping", provider="claude")
        assert delta is None

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        parser = StreamingParser()
        delta = parser.parse_sse_line("data: {invalid json}", provider="claude")
        assert delta is None

    def test_parse_stream_full(self):
        """Test parsing a complete stream."""
        parser = StreamingParser()
        lines = [
            'data: {"type": "content_block_delta", "delta": {"text": "Hello"}}',
            'data: {"type": "content_block_delta", "delta": {"text": " world"}}',
            'data: {"type": "message_stop"}',
        ]

        deltas = list(parser.parse_stream(iter(lines), provider="claude"))
        assert len(deltas) == 3
        assert deltas[0].token == "Hello"
        assert deltas[1].token == " world"
        assert deltas[2].is_final is True

    def test_parse_gemini_delta(self):
        """Test parsing Gemini delta."""
        parser = StreamingParser()
        line = 'data: {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}'
        delta = parser.parse_sse_line(line, provider="gemini")

        assert delta is not None
        assert delta.token == "Hello"

    def test_parse_unknown_provider(self):
        """Test parsing with unknown provider returns None."""
        parser = StreamingParser()
        line = 'data: {"test": "data"}'
        delta = parser.parse_sse_line(line, provider="unknown")
        assert delta is None
