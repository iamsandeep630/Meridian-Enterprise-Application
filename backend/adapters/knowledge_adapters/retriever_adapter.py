"""
Knowledge Base Hybrid Retriever Secondary Adapter
Implements IKnowledgeBasePort using FAISS dense vectors + BM25 sparse search.
"""
from typing import Any

from ports.knowledge import IKnowledgeBasePort
from rag.retriever import HybridRetriever


class HybridRetrieverAdapter(IKnowledgeBasePort):
    """Adapter wrapping HybridRetriever to satisfy IKnowledgeBasePort."""

    def __init__(self, retriever_instance=None):
        self._retriever = retriever_instance or HybridRetriever.get_instance()

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self._retriever.search(query=query, top_k=top_k)
