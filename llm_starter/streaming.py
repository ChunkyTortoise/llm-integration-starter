"""Server-Sent Events (SSE) streaming for LLM responses."""

from __future__ import annotations

import json
from dataclasses import dataclass

from llm_starter.mock_llm import MockLLM


@dataclass
class StreamEvent:
    """A single SSE event."""

    event: str  # "message", "done", "error"
    data: str
    id: str = ""

    def format_sse(self) -> str:
        """Format as an SSE event string."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.event}")
        lines.append(f"data: {self.data}")
        lines.append("")
        return "\n".join(lines) + "\n"


def format_sse_event(event: str, data: str, event_id: str = "") -> str:
    """Format a single SSE event string."""
    return StreamEvent(event=event, data=data, id=event_id).format_sse()


class StreamingClient:
    """Streaming LLM client with SSE event generation.

    Produces Server-Sent Events for real-time UI updates.
    """

    def __init__(self, llm: MockLLM | None = None):
        self.llm = llm or MockLLM()

    def stream_completion(
        self,
        prompt: str,
        model: str = "mock-gpt-4",
    ) -> list[StreamEvent]:
        """Stream a completion as SSE events.

        Returns a list of StreamEvents (message events for each chunk, then a done event).
        """
        chunks = self.llm.stream(prompt, model=model)
        events = []
        for i, chunk in enumerate(chunks):
            events.append(
                StreamEvent(
                    event="message",
                    data=json.dumps({"chunk": chunk, "index": i}),
                    id=str(i),
                )
            )
        events.append(
            StreamEvent(
                event="done",
                data=json.dumps({"total_chunks": len(chunks)}),
                id=str(len(chunks)),
            )
        )
        return events

    def stream_to_string(self, prompt: str, model: str = "mock-gpt-4") -> str:
        """Stream and collect into a single string."""
        chunks = self.llm.stream(prompt, model=model)
        return " ".join(chunks)

    def create_endpoint(self) -> dict:
        """Create a FastAPI SSE streaming endpoint configuration."""
        client = self

        async def handler(prompt: str, model: str = "mock-gpt-4"):
            events = client.stream_completion(prompt, model=model)
            return [e.format_sse() for e in events]

        return {"path": "/api/stream", "method": "POST", "handler": handler}
