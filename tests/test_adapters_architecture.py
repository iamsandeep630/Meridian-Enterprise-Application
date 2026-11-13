"""
Unit tests for Meridian Enterprise Application Hexagonal Architecture Adapters.
Verifies:
1. Conformance of each adapter to its corresponding port Protocol.
2. Direct imports from domain-scoped adapter subpackages.
3. Central exports from adapters.__init__.py.
4. Container service registration and dependency injection.
"""
import sys
import unittest
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from adapters import (
    HybridRetrieverAdapter as RootRetrieverAdapter,
)
from adapters import (
    JiraCloudAdapter as RootJiraAdapter,
)
from adapters import (
    MeshCentralAdapter as RootMeshAdapter,
)
from adapters import (
    SSEBroadcasterAdapter as RootSSEAdapter,
)
from adapters.knowledge_adapters import HybridRetrieverAdapter
from adapters.notification_adapters import SSEBroadcasterAdapter
from adapters.remediation_adapters import MeshCentralAdapter
from adapters.ticketing_adapters import JiraCloudAdapter
from container import Container
from ports.knowledge import IKnowledgeBasePort
from ports.notifications import INotificationPort
from ports.remediation import IRemoteRemediationPort
from ports.ticketing import ITicketingPort


class TestAdaptersArchitecture(unittest.TestCase):

    def test_ticketing_adapter_conformance(self):
        """Verify JiraCloudAdapter satisfies ITicketingPort interface."""
        adapter = JiraCloudAdapter()
        self.assertIsInstance(adapter, ITicketingPort)
        self.assertTrue(hasattr(adapter, "create_ticket"))
        self.assertTrue(hasattr(adapter, "get_ticket"))
        self.assertTrue(hasattr(adapter, "update_ticket"))

    def test_remediation_adapter_conformance(self):
        """Verify MeshCentralAdapter satisfies IRemoteRemediationPort interface."""
        adapter = MeshCentralAdapter()
        self.assertIsInstance(adapter, IRemoteRemediationPort)
        self.assertTrue(hasattr(adapter, "list_managed_devices"))
        self.assertTrue(hasattr(adapter, "find_device"))
        self.assertTrue(hasattr(adapter, "clear_zoom_cache"))
        self.assertTrue(hasattr(adapter, "create_sharing_link"))

    def test_knowledge_adapter_conformance(self):
        """Verify HybridRetrieverAdapter satisfies IKnowledgeBasePort interface."""
        # Use mock retriever to avoid loading heavy FAISS index during quick test
        from unittest.mock import MagicMock
        mock_retriever = MagicMock()
        adapter = HybridRetrieverAdapter(retriever_instance=mock_retriever)
        self.assertIsInstance(adapter, IKnowledgeBasePort)
        self.assertTrue(hasattr(adapter, "search"))

    def test_notification_adapter_conformance(self):
        """Verify SSEBroadcasterAdapter satisfies INotificationPort interface."""
        adapter = SSEBroadcasterAdapter()
        self.assertIsInstance(adapter, INotificationPort)
        self.assertTrue(hasattr(adapter, "broadcast_conversation"))
        self.assertTrue(hasattr(adapter, "broadcast_dashboard"))

    def test_package_exports_consistency(self):
        """Verify root adapters package re-exports the exact classes from subpackages."""
        self.assertIs(RootJiraAdapter, JiraCloudAdapter)
        self.assertIs(RootMeshAdapter, MeshCentralAdapter)
        self.assertIs(RootRetrieverAdapter, HybridRetrieverAdapter)
        self.assertIs(RootSSEAdapter, SSEBroadcasterAdapter)

    def test_rag_pipeline_modularization(self):
        """Verify RAG pipeline module exports."""
        from agents.tools import search_knowledge_base
        from rag.retriever import HybridRetriever as RAGRetriever
        self.assertTrue(callable(search_knowledge_base))
        self.assertTrue(hasattr(RAGRetriever, "search"))

    def test_container_dependency_resolution(self):
        """Verify Container registers and returns concrete port adapters."""
        self.assertIsInstance(Container.get_ticketing_port(), ITicketingPort)
        self.assertIsInstance(Container.get_remediation_port(), IRemoteRemediationPort)
        self.assertIsInstance(Container.get_knowledge_port(), IKnowledgeBasePort)
        self.assertIsInstance(Container.get_notification_port(), INotificationPort)


if __name__ == "__main__":
    unittest.main()
