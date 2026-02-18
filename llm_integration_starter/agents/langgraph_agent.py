"""LangGraph-based ReAct agent template.

Demonstrates how to build a stateful agent using LangGraph's StateGraph
on top of the UnifiedLLMClient. Provides a minimal but production-ready
ReAct (Reason + Act) loop with:

- Typed state via TypedDict
- Tool registry backed by ToolDefinition
- Conditional edge routing (tool call → execute → next step)
- Clean run() interface matching BaseAgent conventions

Install LangGraph extras:
    pip install "ai-agent-starter-kit[agents]"

Usage::

    from llm_integration_starter.agents.langgraph_agent import LangGraphReActAgent

    def add(a: int, b: int) -> int:
        return a + b

    agent = LangGraphReActAgent(tools={"add": add})
    result = agent.run("What is 42 + 58?")
    print(result.output)   # "100"
"""

from __future__ import annotations

import json
from typing import Any, Callable, TypedDict

from llm_integration_starter.agents.base import AgentResult, BaseAgent
from llm_integration_starter.client import UnifiedLLMClient
from llm_integration_starter.function_calling import ToolDefinition

try:
    from langgraph.graph import END, StateGraph
    _LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LANGGRAPH_AVAILABLE = False


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    """Mutable state threaded through the graph."""

    messages: list[dict[str, str]]      # conversation turns
    tool_calls: list[dict[str, Any]]    # pending tool calls from LLM
    tool_results: list[dict[str, Any]]  # results from executed tools
    final_output: str                   # set when the agent is done


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class LangGraphReActAgent(BaseAgent):
    """Stateful ReAct agent built on LangGraph StateGraph.

    The graph has three nodes:
    1. ``reason`` — calls the LLM; may return tool calls or a final answer
    2. ``act`` — executes tool calls and appends results to state
    3. ``END`` — graph terminates when the LLM returns no tool calls

    Args:
        client: UnifiedLLMClient to use (defaults to mock provider).
        tools: dict mapping tool name → Python callable. Each callable must
            have a docstring (used as the tool description) and type-annotated
            parameters (used to build ToolDefinition schemas).
        system_prompt: Override the default ReAct system prompt.
        max_iterations: Hard cap on reason→act cycles (default: 10).
    """

    def __init__(
        self,
        client: UnifiedLLMClient | None = None,
        tools: dict[str, Callable[..., Any]] | None = None,
        system_prompt: str | None = None,
        max_iterations: int = 10,
    ) -> None:
        super().__init__(client)
        self._tool_fns: dict[str, Callable[..., Any]] = tools or {}
        self._system_prompt_override = system_prompt
        self.max_iterations = max_iterations
        self._tool_defs: list[ToolDefinition] = [
            _callable_to_tool_def(name, fn) for name, fn in self._tool_fns.items()
        ]
        if _LANGGRAPH_AVAILABLE:
            self._graph = self._build_graph()
        else:
            self._graph = None

    # -- BaseAgent interface -------------------------------------------------

    @property
    def system_prompt(self) -> str:
        if self._system_prompt_override:
            return self._system_prompt_override
        tool_names = ", ".join(self._tool_fns.keys()) if self._tool_fns else "none"
        return (
            "You are a helpful assistant that solves problems step by step. "
            f"Available tools: {tool_names}. "
            "Use tools when needed. When you have a final answer, respond directly."
        )

    @property
    def tools(self) -> list[ToolDefinition]:
        return self._tool_defs

    def run(self, user_input: str, history: list[dict] | None = None, **kwargs) -> AgentResult:
        """Run the ReAct agent on *user_input*.

        Args:
            user_input: The user's query or instruction.
            history: Optional prior conversation turns.

        Returns:
            AgentResult with final output and metadata.
        """
        if not _LANGGRAPH_AVAILABLE:
            # Graceful fallback: simple single-shot LLM call
            messages = self._build_messages(user_input, history)
            response = self.client.complete(messages)
            return AgentResult(
                output=response.text,
                raw_response=response,
                metadata={"langgraph_available": False, "fallback": True},
            )

        initial_state: AgentState = {
            "messages": self._build_messages(user_input, history),
            "tool_calls": [],
            "tool_results": [],
            "final_output": "",
        }

        final_state = self._graph.invoke(initial_state)
        output = final_state.get("final_output", "")

        # Build a synthetic LLMResponse for BaseAgent compatibility
        from llm_integration_starter.client import LLMResponse
        synthetic_response = LLMResponse(
            text=output,
            model="langgraph",
            provider="langgraph",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            latency_ms=0.0,
        )

        return AgentResult(
            output=output,
            raw_response=synthetic_response,
            metadata={
                "langgraph_available": True,
                "iterations": len(final_state.get("tool_results", [])),
                "tools_used": [
                    tr["tool"]
                    for tr in final_state.get("tool_results", [])
                ],
            },
        )

    # -- Graph construction --------------------------------------------------

    def _build_graph(self) -> "StateGraph":
        """Build a StateGraph with reason → act → END routing."""
        graph: StateGraph = StateGraph(AgentState)

        graph.add_node("reason", self._reason_node)
        graph.add_node("act", self._act_node)

        graph.set_entry_point("reason")

        # After reasoning: if tool calls present → act, else → END
        graph.add_conditional_edges(
            "reason",
            lambda state: "act" if state.get("tool_calls") else END,
        )
        # After acting: always loop back to reason
        graph.add_edge("act", "reason")

        return graph.compile()

    # -- Node implementations ------------------------------------------------

    def _reason_node(self, state: AgentState) -> AgentState:
        """Call the LLM; parse tool calls or capture final answer."""
        iteration = len(state.get("tool_results", []))
        if iteration >= self.max_iterations:
            # Force termination
            return {**state, "tool_calls": [], "final_output": state.get("final_output", "Max iterations reached.")}

        response = self.client.complete(
            state["messages"],
            tools=self._tool_defs if self._tool_defs else None,
        )

        # Extract tool calls from the raw response if present
        raw = getattr(response, "raw", None) or {}
        tool_calls = raw.get("tool_calls", [])

        if tool_calls:
            return {**state, "tool_calls": tool_calls, "final_output": ""}

        # No tool calls → final answer
        return {**state, "tool_calls": [], "final_output": response.text}

    def _act_node(self, state: AgentState) -> AgentState:
        """Execute pending tool calls and append results to messages."""
        tool_results = list(state.get("tool_results", []))
        messages = list(state["messages"])
        new_tool_calls = []

        for tc in state.get("tool_calls", []):
            fn_info = tc.get("function", {})
            name = fn_info.get("name", "")
            args_raw = fn_info.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except (json.JSONDecodeError, TypeError):
                args = {}

            result: Any
            if name in self._tool_fns:
                try:
                    result = self._tool_fns[name](**args)
                except Exception as exc:  # noqa: BLE001
                    result = f"Tool error: {exc}"
            else:
                result = f"Unknown tool: {name}"

            tool_results.append({"tool": name, "args": args, "result": result})
            new_tool_calls.append(tc)

            # Append tool result as an assistant/tool message
            messages.append({"role": "tool", "content": str(result), "name": name})

        return {**state, "tool_calls": [], "tool_results": tool_results, "messages": messages}


# ---------------------------------------------------------------------------
# Helper: build ToolDefinition from a Python callable
# ---------------------------------------------------------------------------

def _callable_to_tool_def(name: str, fn: Callable[..., Any]) -> ToolDefinition:
    """Create a ToolDefinition from a Python function's signature and docstring."""
    import inspect
    import typing

    doc_lines = (fn.__doc__ or "").strip().splitlines()
    description = (doc_lines[0] if doc_lines else "") or f"Execute {name}"
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    _type_map = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # Use get_type_hints() to resolve PEP 563 string annotations
    try:
        type_hints = typing.get_type_hints(fn)
    except Exception:  # noqa: BLE001
        type_hints = {}

    for param_name, param in sig.parameters.items():
        annotation = type_hints.get(param_name, param.annotation)
        json_type = _type_map.get(annotation, "string")
        properties[param_name] = {"type": json_type, "description": param_name}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return ToolDefinition.create(
        name=name,
        description=description,
        properties=properties,
        required=required,
    )
