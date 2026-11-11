"""
Notification & Event Broadcast Port (Outbound Driven Port)
Defines abstract interface for real-time streaming, SSE, and inter-service event publishing.
"""
from typing import Protocol, runtime_checkable, Dict, Any


@runtime_checkable
class INotificationPort(Protocol):
    """Outbound port for broadcasting live events to connected clients."""

    async def broadcast_conversation(self, conversation_id: str, payload: Dict[str, Any]) -> None:
        """Broadcasts an event to participants in a specific conversation session."""
        ...

    async def broadcast_dashboard(self, payload: Dict[str, Any]) -> None:
        """Broadcasts a live update to listening support engineer dashboards."""
        ...
