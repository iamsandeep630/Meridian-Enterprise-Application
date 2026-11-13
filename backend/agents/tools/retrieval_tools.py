"""
Retrieval & Knowledge Base Tools for Meridian Enterprise Agents.
Delegates to IKnowledgeBasePort via the Hexagonal Container.
"""
from container import Container


def search_knowledge_base(query: str, top_k: int = 5) -> list[dict]:
    """
    Searches the Confluence knowledge base using hybrid dense + lexical search.
    Delegates to IKnowledgeBasePort.
    """
    return Container.get_knowledge_port().search(query, top_k=top_k)

