"""
L2 Support Escalation Tools for Meridian Enterprise Agents.
Integrates with escalation_service for human engineer handoff.
"""

from services import escalation_service


async def escalate_to_l2_support(
    session_id: int,
    user_email: str,
    issue_summary: str,
    execution_details: str,
    device_id: str | None = None,
    requires_remote_desktop: bool | None = None
) -> dict:
    """
    Escalates an unresolved issue to a human Support Engineer.
    Transitions ticket to 'L2 Confirmed', generates ephemeral remote desktop sharing link if needed,
    and updates the Support Engineer live dashboard.
    """
    return await escalation_service.escalate_session(
        session_id=session_id,
        user_email=user_email,
        issue_summary=issue_summary,
        execution_details=execution_details,
        device_id=device_id,
        requires_remote_desktop=requires_remote_desktop
    )
