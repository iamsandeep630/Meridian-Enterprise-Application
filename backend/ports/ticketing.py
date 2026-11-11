"""
Ticketing Port (Outbound Driven Port)
Defines abstract interface for issue tracking systems (e.g., Atlassian Jira Cloud, ServiceNow).
"""
from typing import Protocol, runtime_checkable, Optional, Dict, Any, List


@runtime_checkable
class ITicketingPort(Protocol):
    """Outbound port for ticketing operations."""

    def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        components: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Creates a new ticket in the ticketing backend."""
        ...

    def get_ticket(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of an existing ticket."""
        ...

    def update_ticket(self, ticket_key: str, fields: Dict[str, Any]) -> bool:
        """Updates fields on an existing ticket."""
        ...

