"""Tests for SimpleRAG pipeline."""

from __future__ import annotations

from llm_starter.mock_llm import MockLLM
from llm_starter.rag_pipeline import RAGResult, SimpleRAG


class TestSimpleRAG:
    """Tests for SimpleRAG."""

    def _sample_docs(self) -> list[str]:
        return [
            "Python is a programming language used for web development and data science.",
            "JavaScript runs in browsers and powers modern web applications.",
            "PostgreSQL is a powerful open-source relational database system.",
            "Redis is an in-memory data store used for caching and messaging.",
            "Docker containers package applications with their dependencies.",
        ]

    def test_ingest_documents(self) -> None:
        rag = SimpleRAG()
        count = rag.ingest(self._sample_docs())
        assert count == 5

    def test_retrieve_relevant(self) -> None:
        rag = SimpleRAG()
        rag.ingest(self._sample_docs())
        results = rag.retrieve("What is Python?")
        assert len(results) > 0
        # First result should be about Python
        assert "Python" in results[0][0]

    def test_retrieve_empty(self) -> None:
        rag = SimpleRAG()
        results = rag.retrieve("anything")
        assert results == []

    def test_query_produces_answer(self) -> None:
        llm = MockLLM(default_response="Python is a programming language.")
        rag = SimpleRAG(llm)
        rag.ingest(self._sample_docs())
        result = rag.query("What is Python?")
        assert result.answer == "Python is a programming language."
        assert result.num_sources > 0

    def test_query_no_docs(self) -> None:
        rag = SimpleRAG()
        result = rag.query("anything")
        assert result.answer == "No relevant documents found."
        assert result.num_sources == 0

    def test_document_count(self) -> None:
        rag = SimpleRAG()
        assert rag.document_count == 0
        rag.ingest(self._sample_docs())
        assert rag.document_count == 5

    def test_top_k_respected(self) -> None:
        rag = SimpleRAG(top_k=2)
        rag.ingest(self._sample_docs())
        results = rag.retrieve("programming language database")
        assert len(results) <= 2

    def test_scores_sorted(self) -> None:
        rag = SimpleRAG(top_k=5)
        rag.ingest(self._sample_docs())
        results = rag.retrieve("programming language")
        if len(results) > 1:
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)


class TestRAGResult:
    """Tests for RAGResult dataclass."""

    def test_result_fields(self) -> None:
        result = RAGResult(
            query="test",
            answer="answer",
            sources=["doc1"],
            scores=[0.95],
            num_sources=1,
        )
        assert result.query == "test"
        assert result.answer == "answer"

    def test_sources_match_count(self) -> None:
        result = RAGResult(
            query="q",
            answer="a",
            sources=["s1", "s2"],
            scores=[0.9, 0.8],
            num_sources=2,
        )
        assert len(result.sources) == result.num_sources

    def test_empty_result(self) -> None:
        result = RAGResult(query="q", answer="none", sources=[], scores=[], num_sources=0)
        assert result.num_sources == 0
        assert result.sources == []

    def test_query_preserved(self) -> None:
        result = RAGResult(
            query="original question",
            answer="a",
            sources=[],
            scores=[],
            num_sources=0,
        )
        assert result.query == "original question"
