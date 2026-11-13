"""
Adapters Package - Hexagonal Architecture Secondary Adapters for Meridian Enterprise Application.
Organized into port-specific adapter sub-packages for modularity, clean boundaries, and easy extension.

Sub-packages:
- ticketing_adapters: JiraCloudAdapter (implements ITicketingPort)
- remediation_adapters: MeshCentralAdapter (implements IRemoteRemediationPort)
- knowledge_adapters: HybridRetrieverAdapter (implements IKnowledgeBasePort)
- notification_adapters: SSEBroadcasterAdapter (implements INotificationPort)
"""
from adapters.knowledge_adapters import HybridRetrieverAdapter
from adapters.notification_adapters import SSEBroadcasterAdapter
from adapters.remediation_adapters import MeshCentralAdapter
from adapters.ticketing_adapters import JiraCloudAdapter

__all__ = [
    "HybridRetrieverAdapter",
    "JiraCloudAdapter",
    "MeshCentralAdapter",
    "SSEBroadcasterAdapter"
]
