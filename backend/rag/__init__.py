"""
RAG (Retrieval-Augmented Generation) Pipeline Package for Meridian Enterprise Helpdesk.
Encapsulates document chunking, vector indexing, and hybrid retrieval.
"""
from rag.chunker import chunk_all_docs, chunk_markdown_article
from rag.indexer import build_all
from rag.retriever import HybridRetriever

__all__ = [
    "HybridRetriever",
    "build_all",
    "chunk_all_docs",
    "chunk_markdown_article",
]
