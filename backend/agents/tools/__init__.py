"""
Agent Tools Package for Meridian Enterprise Helpdesk.
Consolidates modular toolsets across retrieval, remediation, ticketing, and escalation.
"""
from agents.tools.escalation_tools import escalate_to_l2_support
from agents.tools.remediation_tools import (
    clear_zoom_cache,
    create_device_sharing_link,
    get_device_info,
    list_managed_devices,
)
from agents.tools.retrieval_tools import search_knowledge_base
from agents.tools.ticketing_tools import jira_create_ticket, jira_update_ticket

FRIENDLY_TOOL_STATUS: dict[str, str] = {
    "search_knowledge_base": "Searching knowledge base...",
    "jira_create_ticket": "Preparing remediation session...",
    "jira_update_ticket": "Updating diagnostic records...",
    "clear_zoom_cache": "Executing remote cache clear on device...",
    "escalate_to_l2_support": "Escalating to human Support Engineer...",
    "list_managed_devices": "Checking device connectivity...",
    "get_device_info": "Accessing device details...",
    "create_device_sharing_link": "Generating secure remote desktop link...",
}


def get_friendly_tool_status(tool_name: str) -> str:
    """Returns human-friendly processing status message for background tools."""
    return FRIENDLY_TOOL_STATUS.get(tool_name, "Processing...")


TOOL_CATALOG = {
    "search_knowledge_base": {
        "name": "search_knowledge_base",
        "description": "Searches Confluence knowledge base for articles, guides, policies, and troubleshooting procedures.",
        "category": "knowledge",
        "automatable": True,
        "function": search_knowledge_base,
    },
    "clear_zoom_cache": {
        "name": "clear_zoom_cache",
        "description": "Remotely clears Zoom cache and temporary files on user endpoint via MeshCentral.",
        "category": "remediation",
        "automatable": True,
        "function": clear_zoom_cache,
    },
    "list_managed_devices": {
        "name": "list_managed_devices",
        "description": "Discovers online managed endpoints via MeshCentral.",
        "category": "device",
        "automatable": True,
        "function": list_managed_devices,
    },
    "get_device_info": {
        "name": "get_device_info",
        "description": "Gets hardware and OS specs for a managed device.",
        "category": "device",
        "automatable": True,
        "function": get_device_info,
    },
    "create_device_sharing_link": {
        "name": "create_device_sharing_link",
        "description": "Generates a 30-minute self-expiring remote desktop link for live human assistance.",
        "category": "device",
        "automatable": True,
        "function": create_device_sharing_link,
    },
    "jira_create_ticket": {
        "name": "jira_create_ticket",
        "description": "Silently creates a background tracking ticket in Jira.",
        "category": "tracking",
        "automatable": True,
        "function": jira_create_ticket,
    },
    "jira_update_ticket": {
        "name": "jira_update_ticket",
        "description": "Silently updates a Jira tracking ticket status or comments.",
        "category": "tracking",
        "automatable": True,
        "function": jira_update_ticket,
    },
    "escalate_to_l2_support": {
        "name": "escalate_to_l2_support",
        "description": "Escalates unresolved issues to a human L2 Support Engineer.",
        "category": "escalation",
        "automatable": True,
        "function": escalate_to_l2_support,
    },
}

__all__ = [
    "FRIENDLY_TOOL_STATUS",
    "TOOL_CATALOG",
    "clear_zoom_cache",
    "create_device_sharing_link",
    "escalate_to_l2_support",
    "get_device_info",
    "get_friendly_tool_status",
    "jira_create_ticket",
    "jira_update_ticket",
    "list_managed_devices",
    "search_knowledge_base",
]

