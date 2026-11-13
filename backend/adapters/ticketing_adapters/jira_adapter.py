"""
Jira Cloud Secondary Adapter
Implements ITicketingPort using Atlassian Jira Cloud REST API.
"""
from typing import Any

from ports.ticketing import ITicketingPort
from services import jira_service


class JiraCloudAdapter(ITicketingPort):
    """Adapter wrapping JiraService to satisfy ITicketingPort."""

    def __init__(self, service=jira_service):
        self._service = service

    def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        components: list[str] | None = None,
        labels: list[str] | None = None,
        custom_fields: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._service.create_ticket(
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            components=components,
            labels=labels,
            custom_fields=custom_fields
        )

    def get_ticket(self, ticket_key: str) -> dict[str, Any] | None:
        return self._service.get_ticket(ticket_key)

    def update_ticket(self, ticket_key: str, fields: dict[str, Any]) -> bool:
        return self._service.update_ticket(ticket_key, fields)
