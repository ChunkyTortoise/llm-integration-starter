"""Streaming response parser."""
from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class StreamDelta:
    token: str
    is_final: bool
    latency_ms: float

class StreamingParser:
    def __init__(self):
        self.start_time = 0.0

    def parse_sse_line(self, line: str, provider: str = "claude"):
        if not line.startswith("data: "):
            return None
        json_str = line[6:].strip()
        if json_str == "[DONE]":
            return StreamDelta(token="", is_final=True, latency_ms=0.0)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None
        if provider == "claude":
            return self._parse_claude_delta(data)
        elif provider == "openai":
            return self._parse_openai_delta(data)
        elif provider == "gemini":
            return self._parse_gemini_delta(data)
        return None

    def _parse_claude_delta(self, data: dict):
        event_type = data.get("type", "")
        if event_type == "content_block_delta":
            text = data.get("delta", {}).get("text", "")
            if text:
                return StreamDelta(token=text, is_final=False, latency_ms=0.0)
        elif event_type == "message_stop":
            return StreamDelta(token="", is_final=True, latency_ms=0.0)
        return None

    def _parse_openai_delta(self, data: dict):
        choices = data.get("choices", [])
        if not choices:
            return None
        choice = choices[0]
        content = choice.get("delta", {}).get("content", "")
        if content:
            return StreamDelta(token=content, is_final=False, latency_ms=0.0)
        if choice.get("finish_reason"):
            return StreamDelta(token="", is_final=True, latency_ms=0.0)
        return None

    def _parse_gemini_delta(self, data: dict):
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            text = parts[0].get("text", "")
            if text:
                return StreamDelta(token=text, is_final=False, latency_ms=0.0)
        if candidates[0].get("finishReason"):
            return StreamDelta(token="", is_final=True, latency_ms=0.0)
        return None

    def parse_stream(self, lines, provider: str = "claude"):
        for line in lines:
            delta = self.parse_sse_line(line, provider=provider)
            if delta:
                yield delta
                if delta.is_final:
                    break
