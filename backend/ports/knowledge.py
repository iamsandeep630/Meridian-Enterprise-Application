"""
Knowledge Base Port (Outbound Driven Port)
Defines abstract interface for RAG document indexing and retrieval systems.
"""
from typing import Protocol, runtime_checkable, List, Dict, Any


@runtime_checkable
class IKnowledgeBasePort(Protocol):
    """Outbound port for searching internal documentation and SOPs."""

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Executes hybrid vector + lexical retrieval over indexed documents."""
        ...
