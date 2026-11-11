"""
Remote Remediation Port (Outbound Driven Port)
Defines abstract interface for endpoint device discovery, command execution, and remote desktop assist.
"""
from typing import Protocol, runtime_checkable, Optional, Dict, Any, List


@runtime_checkable
class IRemoteRemediationPort(Protocol):
    """Outbound port for remote device management and remediation."""

    def list_managed_devices(self) -> Dict[str, Any]:
        """Lists all online and offline managed endpoints."""
        ...

    def find_device(self, devices: List[Dict[str, Any]], query: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Resolves target machine node record from search criteria."""
        ...

    def clear_zoom_cache(self, device_id: Optional[str] = None, computer_name: Optional[str] = None) -> Dict[str, Any]:
        """Executes remote script to stop frozen Zoom processes and purge cached temp files."""
        ...

    def create_sharing_link(self, device_id: str, duration_minutes: int = 30) -> Dict[str, Any]:
        """Generates an ephemeral, time-bounded remote desktop access link."""
        ...
