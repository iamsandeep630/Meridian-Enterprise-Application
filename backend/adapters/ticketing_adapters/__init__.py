"""
Ticketing Adapters - Implementations of ITicketingPort.
Provides pluggable adapters for Atlassian Jira Cloud and other issue management services.
"""
from adapters.ticketing_adapters.jira_adapter import JiraCloudAdapter

__all__ = [
    "JiraCloudAdapter"
]

