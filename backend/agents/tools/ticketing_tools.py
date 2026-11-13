"""
Ticketing & Issue Tracking Tools for Meridian Enterprise Agents.
Integrates with Jira Cloud for silent issue lifecycle management.
"""

from services import jira_service


def jira_create_ticket(
    session_id: int,
    user_email: str,
    user_query: str,
    chat_history: list[dict],
    device_info: dict | None = None,
    sharing_link: str | None = None,
    chat_link: str | None = None,
    initial_status: str = "In Progress",
    assignee_type: str = "Bot"
) -> dict:
    """
    Creates a Jira ticket silently in the background for dashboard tracking.
    Sets status to 'In Progress' and assignee to 'Bot'.
    """
    return jira_service.create_jira_issue(
        session_id=session_id,
        user_email=user_email,
        user_query=user_query,
        chat_history=chat_history,
        device_info=device_info,
        sharing_link=sharing_link,
        chat_link=chat_link,
        initial_status=initial_status,
        assignee_type=assignee_type
    )


def jira_update_ticket(ticket_key: str, status: str | None = None, comment: str | None = None) -> dict:
    """
    Updates a Jira ticket silently in the background (e.g. marking as 'Bot Resolved').
    """
    return jira_service.update_jira_ticket(ticket_key=ticket_key, status=status, comment=comment)
