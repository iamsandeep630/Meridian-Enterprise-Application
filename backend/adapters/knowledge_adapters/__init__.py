"""
Knowledge Base Adapters - Implementations of IKnowledgeBasePort.
Provides pluggable adapters for RAG document retrieval (e.g., FAISS + BM25 Hybrid Retriever).
"""
from adapters.knowledge_adapters.retriever_adapter import HybridRetrieverAdapter

__all__ = [
    "HybridRetrieverAdapter"
]

