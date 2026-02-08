"""LLM Integration Starter — Streamlit demo with 5 tabs."""

from __future__ import annotations

import json
import os
import time

import streamlit as st

from llm_starter.completion import CompletionClient
from llm_starter.cost_tracker import CostTracker
from llm_starter.function_calling import FunctionCallingClient
from llm_starter.latency_tracker import LatencyTracker
from llm_starter.mock_llm import MockLLM
from llm_starter.rag_pipeline import SimpleRAG
from llm_starter.streaming import StreamingClient

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LLM Integration Starter",
    page_icon="*",
    layout="wide",
)

st.title("LLM Integration Starter")
st.caption("Production-ready LLM integration patterns — no API keys required")


# ── Shared state ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_llm() -> MockLLM:
    llm = MockLLM(
        default_response="This is a demo response from MockLLM. "
        "In production, this would be a real LLM API call.",
        latency_ms=15.0,
    )
    llm.set_response("hello", "Hello! I'm your AI assistant. How can I help you today?")
    llm.set_response(
        "python",
        "Python is a versatile programming language great for AI and web dev.",
    )
    llm.set_response(
        "pricing",
        "Our plans start at $49/month for Starter, $199/month for Professional, "
        "and $499/month for Enterprise.",
    )
    return llm


@st.cache_resource
def get_cost_tracker() -> CostTracker:
    return CostTracker()


@st.cache_resource
def get_latency_tracker() -> LatencyTracker:
    return LatencyTracker(window_seconds=600.0)


def load_demo_docs() -> list[str]:
    """Load demo documents from demo_data/."""
    docs = []
    demo_dir = os.path.join(os.path.dirname(__file__), "demo_data")
    if os.path.isdir(demo_dir):
        for fname in sorted(os.listdir(demo_dir)):
            fpath = os.path.join(demo_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath) as f:
                    content = f.read()
                # Split into paragraphs for finer retrieval
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                docs.extend(paragraphs)
    return docs


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Completion", "Streaming", "Function Calling", "RAG", "Dashboard"]
)

llm = get_llm()
cost_tracker = get_cost_tracker()
latency_tracker = get_latency_tracker()

# ── Tab 1: Completion ────────────────────────────────────────────────────────
with tab1:
    st.header("Basic Completion")
    st.markdown("Send a prompt and receive a complete response.")

    col1, col2 = st.columns([2, 1])
    with col1:
        prompt = st.text_area("Prompt", value="Tell me about Python", height=100, key="comp_prompt")
    with col2:
        system = st.text_input("System prompt (optional)", value="You are a helpful assistant.")

    if st.button("Complete", key="comp_btn"):
        client = CompletionClient(llm)
        start = time.perf_counter()
        result = client.complete(prompt, system=system)
        elapsed = (time.perf_counter() - start) * 1000

        # Track
        cost_tracker.record(result.model, result.prompt_tokens, result.completion_tokens)
        latency_tracker.record(result.latency_ms)

        st.success(result.content)
        st.json(
            {
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "latency_ms": round(result.latency_ms, 2),
            }
        )

# ── Tab 2: Streaming ────────────────────────────────────────────────────────
with tab2:
    st.header("SSE Streaming")
    st.markdown("Watch the response arrive chunk by chunk as Server-Sent Events.")

    stream_prompt = st.text_area(
        "Prompt", value="Explain AI briefly", height=100, key="stream_prompt"
    )

    if st.button("Stream", key="stream_btn"):
        client = StreamingClient(llm)
        events = client.stream_completion(stream_prompt)

        # Display chunks progressively
        placeholder = st.empty()
        collected = []
        for event in events:
            if event.event == "message":
                data = json.loads(event.data)
                collected.append(data["chunk"])
                placeholder.markdown(" ".join(collected) + " |")
                time.sleep(0.05)  # visual effect
            elif event.event == "done":
                placeholder.markdown(" ".join(collected))

        st.caption(f"{len(events) - 1} chunks streamed")

        with st.expander("Raw SSE events"):
            for event in events:
                st.code(event.format_sse(), language="text")

# ── Tab 3: Function Calling ─────────────────────────────────────────────────
with tab3:
    st.header("Function Calling")
    st.markdown("The LLM selects and executes tools from a registered set.")

    fc_client = FunctionCallingClient(llm)

    with st.expander("Available tools", expanded=True):
        for tool in fc_client.get_tools():
            st.markdown(f"**{tool.name}** — {tool.description}")

    fc_prompt = st.text_input("Prompt", value="Calculate 2 + 2", key="fc_prompt")

    if st.button("Execute", key="fc_btn"):
        results = fc_client.process(fc_prompt)
        for r in results:
            if r.error:
                st.error(f"Tool `{r.tool_name}` error: {r.error}")
            else:
                st.success(f"Tool `{r.tool_name}` returned: {r.result}")
            st.json({"tool": r.tool_name, "arguments": r.arguments, "result": r.result})

    st.divider()
    st.subheader("Direct tool execution")
    col_a, col_b = st.columns(2)
    with col_a:
        expr = st.text_input("Math expression", value="3 * (4 + 5)", key="calc_expr")
        if st.button("Calculate", key="calc_btn"):
            r = fc_client.execute_tool("calculate", {"expression": expr})
            st.write(f"Result: {r.result}")
    with col_b:
        query = st.text_input("Lookup query", value="python", key="lookup_q")
        if st.button("Lookup", key="lookup_btn"):
            r = fc_client.execute_tool("lookup", {"query": query})
            st.write(f"Result: {r.result}")

# ── Tab 4: RAG ──────────────────────────────────────────────────────────────
with tab4:
    st.header("RAG Pipeline")
    st.markdown(
        "Retrieval-Augmented Generation: ingest documents, "
        "retrieve relevant context, generate answers."
    )

    rag = SimpleRAG(llm, top_k=3)
    docs = load_demo_docs()

    if docs:
        count = rag.ingest(docs)
        st.info(f"Ingested {count} document chunks from demo_data/")
    else:
        st.warning("No demo documents found in demo_data/")

    rag_query = st.text_input("Question", value="How much does CloudSync Pro cost?", key="rag_q")

    if st.button("Ask", key="rag_btn") and docs:
        result = rag.query(rag_query)

        cost_tracker.record("mock-gpt-4", 200, 100)
        latency_tracker.record(15.0)

        st.success(result.answer)

        st.subheader("Retrieved sources")
        for i, (src, score) in enumerate(zip(result.sources, result.scores)):
            st.markdown(f"**Source {i + 1}** (score: {score:.4f})")
            st.text(src[:200] + ("..." if len(src) > 200 else ""))

# ── Tab 5: Dashboard ────────────────────────────────────────────────────────
with tab5:
    st.header("Cost & Latency Dashboard")

    col_cost, col_latency = st.columns(2)

    with col_cost:
        st.subheader("Cost Tracking")
        summary = cost_tracker.get_summary()
        if summary.total_requests > 0:
            st.metric("Total Cost", f"${summary.total_cost:.4f}")
            st.metric("Total Requests", summary.total_requests)
            st.metric("Avg Cost/Request", f"${summary.avg_cost_per_request:.6f}")
            st.metric("Daily Projection", f"${summary.daily_projection:.2f}")
            st.metric("Monthly Projection", f"${summary.monthly_projection:.2f}")

            if summary.cost_by_model:
                st.markdown("**Cost by model:**")
                for model, cost in summary.cost_by_model.items():
                    st.write(f"  {model}: ${cost:.6f}")
        else:
            st.info("No cost data yet. Use the other tabs to generate requests.")

    with col_latency:
        st.subheader("Latency Tracking")
        stats = latency_tracker.get_stats()
        if stats.count > 0:
            st.metric("P50 Latency", f"{stats.p50:.1f} ms")
            st.metric("P95 Latency", f"{stats.p95:.1f} ms")
            st.metric("P99 Latency", f"{stats.p99:.1f} ms")
            st.metric("Mean Latency", f"{stats.mean:.1f} ms")
            st.metric("Min / Max", f"{stats.min:.1f} / {stats.max:.1f} ms")
            st.metric("Samples", stats.count)
        else:
            st.info("No latency data yet. Use the other tabs to generate requests.")
