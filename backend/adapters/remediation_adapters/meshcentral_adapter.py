"""
MeshCentral Secondary Adapter
Implements IRemoteRemediationPort using MeshCentral CLI (meshctrl.js) & WebSockets.
"""
from typing import Any

from ports.remediation import IRemoteRemediationPort
from services import meshcentral_service


class MeshCentralAdapter(IRemoteRemediationPort):
    """Adapter wrapping MeshCentralService to satisfy IRemoteRemediationPort."""

    def __init__(self, service=meshcentral_service):
        self._service = service

    def list_managed_devices(self) -> dict[str, Any]:
        return self._service.list_managed_devices()

    def find_device(self, devices: list[dict[str, Any]], query: str | None = None) -> dict[str, Any] | None:
        return self._service.find_device(devices, query=query)

    def clear_zoom_cache(self, device_id: str | None = None, computer_name: str | None = None) -> dict[str, Any]:
        return self._service.clear_zoom_cache(device_id=device_id, computer_name=computer_name)

    def create_sharing_link(self, device_id: str, duration_minutes: int = 30) -> dict[str, Any]:
        return self._service.create_sharing_link(device_id=device_id, duration_minutes=duration_minutes)
