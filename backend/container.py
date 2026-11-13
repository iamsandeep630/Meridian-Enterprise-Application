"""
Dependency Injection Container / Service Registry
Wires Hexagonal Architecture Ports to their concrete Adapters for Meridian Enterprise Application.
"""
from adapters.knowledge_adapters import HybridRetrieverAdapter
from adapters.notification_adapters import SSEBroadcasterAdapter
from adapters.remediation_adapters import MeshCentralAdapter
from adapters.ticketing_adapters import JiraCloudAdapter
from ports.knowledge import IKnowledgeBasePort
from ports.notifications import INotificationPort
from ports.remediation import IRemoteRemediationPort
from ports.ticketing import ITicketingPort


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

