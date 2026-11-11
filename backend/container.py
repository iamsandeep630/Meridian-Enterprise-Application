"""
Dependency Injection Container / Service Registry
Wires Hexagonal Architecture Ports to their concrete Adapters for Meridian Enterprise Application.
"""
from ports.ticketing import ITicketingPort
from ports.remediation import IRemoteRemediationPort
from ports.knowledge import IKnowledgeBasePort
from ports.notifications import INotificationPort

from adapters.jira_adapter import JiraCloudAdapter
from adapters.meshcentral_adapter import MeshCentralAdapter
from adapters.retriever_adapter import HybridRetrieverAdapter
from adapters.sse_adapter import SSEBroadcasterAdapter


class Container:
    """Central container managing port instances."""
    _ticketing_port: ITicketingPort = JiraCloudAdapter()
    _remediation_port: IRemoteRemediationPort = MeshCentralAdapter()
    _knowledge_port: IKnowledgeBasePort = HybridRetrieverAdapter()
    _notification_port: INotificationPort = SSEBroadcasterAdapter()

    @classmethod
    def get_ticketing_port(cls) -> ITicketingPort:
        return cls._ticketing_port

    @classmethod
    def get_remediation_port(cls) -> IRemoteRemediationPort:
        return cls._remediation_port

    @classmethod
    def get_knowledge_port(cls) -> IKnowledgeBasePort:
        return cls._knowledge_port

    @classmethod
    def get_notification_port(cls) -> INotificationPort:
        return cls._notification_port

