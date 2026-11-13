"""
Endpoint Remediation & Device Management Tools for Meridian Enterprise Agents.
Delegates to IRemoteRemediationPort and meshcentral_service.
"""

from container import Container
from services import meshcentral_service


def list_managed_devices() -> dict:
    """Queries MeshCentral for all managed endpoints via IRemoteRemediationPort."""
    return Container.get_remediation_port().list_managed_devices()


def get_device_info(device_id: str | None = None) -> dict:
    """Retrieves detailed hardware and OS information for a specific device."""
    return meshcentral_service.get_device_info(device_id=device_id)


def clear_zoom_cache(device_id: str | None = None) -> dict:
    """
    Executes remote Zoom cache clearing on the user's endpoint via IRemoteRemediationPort.
    Terminates background Zoom processes, purges AppData cache directories,
    and removes temporary files.
    """
    return Container.get_remediation_port().clear_zoom_cache(device_id=device_id)


def create_device_sharing_link(device_id: str | None = None, duration_minutes: int = 30) -> dict:
    """Creates a 30-minute self-expiring remote desktop sharing link via IRemoteRemediationPort."""
    if device_id:
        return Container.get_remediation_port().create_sharing_link(device_id=device_id, duration_minutes=duration_minutes)
    return meshcentral_service.create_device_sharing_link(device_id=device_id, duration_minutes=duration_minutes)
