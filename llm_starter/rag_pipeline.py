"""Simple RAG pipeline: ingest -> TF-IDF embed -> cosine retrieve -> generate."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from llm_starter.mock_llm import MockLLM


@dataclass
class RAGResult:
    """Result of a RAG query."""

    query: str
    answer: str
    sources: list[str]
    scores: list[float]
    num_sources: int


class SimpleRAG:
    """Simple RAG pipeline using TF-IDF for retrieval.

    Ingest documents -> TF-IDF vectorize -> cosine similarity retrieve -> LLM generate.
    """

    def __init__(self, llm: MockLLM | None = None, top_k: int = 3):
        self.llm = llm or MockLLM()
        self.top_k = top_k
        self._documents: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None

    def ingest(self, documents: list[str]) -> int:
        """Ingest documents into the pipeline.

        Returns number of documents ingested.
        """
        self._documents = documents
        if documents:
            self._vectorizer = TfidfVectorizer()
            self._tfidf_matrix = self._vectorizer.fit_transform(documents)
        return len(documents)

    def retrieve(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """Retrieve top-K relevant documents for a query.

        Returns list of (document, score) tuples sorted by relevance.
        """
        if not self._documents or self._vectorizer is None:
            return []

        k = top_k or self.top_k
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        top_indices = np.argsort(scores)[::-1][:k]
        return [(self._documents[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def query(self, question: str, top_k: int | None = None) -> RAGResult:
        """Full RAG pipeline: retrieve + generate."""
        retrieved = self.retrieve(question, top_k)

        if not retrieved:
            return RAGResult(
                query=question,
                answer="No relevant documents found.",
                sources=[],
                scores=[],
                num_sources=0,
            )

        sources = [doc for doc, _ in retrieved]
        scores = [score for _, score in retrieved]

        context = "\n\n".join(sources)
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )

        response = self.llm.complete(prompt)

        return RAGResult(
            query=question,
            answer=response.content,
            sources=sources,
            scores=[round(s, 4) for s in scores],
            num_sources=len(sources),
        )

    @property
    def document_count(self) -> int:
        """Number of ingested documents."""
        return len(self._documents)
