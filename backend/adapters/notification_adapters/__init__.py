"""
Notification Adapters - Implementations of INotificationPort.
Provides pluggable adapters for real-time pub/sub event broadcasting (e.g., Server-Sent Events).
"""
from adapters.notification_adapters.sse_adapter import SSEBroadcasterAdapter

__all__ = [
    "SSEBroadcasterAdapter"
]

