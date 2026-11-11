"""
Server-Sent Events (SSE) Broadcaster Secondary Adapter
Implements INotificationPort for real-time pub/sub distribution.
"""
from typing import Dict, Any
from ports.notifications import INotificationPort
from services.escalation_service import broadcast_conversation, broadcast_dashboard


class SSEBroadcasterAdapter(INotificationPort):
    """Adapter for Server-Sent Events broadcasting."""

    async def broadcast_conversation(self, conversation_id: str, payload: Dict[str, Any]) -> None:
        await broadcast_conversation(conversation_id, payload)

    async def broadcast_dashboard(self, payload: Dict[str, Any]) -> None:
        await broadcast_dashboard(payload)

