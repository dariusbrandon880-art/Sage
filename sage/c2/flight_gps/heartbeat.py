"""Heartbeat expiry and probe-before-reclaim logic."""

from typing import Callable, Dict, Optional

from .models import AirspaceStatus, FlightLifecycle, FlightManifest


class HeartbeatMonitor:
    """Detect stale owners and reclaim only after an owner probe fails."""

    def __init__(self, owner_probe_callback: Optional[Callable[[str], bool]] = None):
        self.owner_probe_callback = owner_probe_callback

    def evaluate_and_reclaim(
        self, registry: Dict[str, FlightManifest], now: Optional[float] = None
    ) -> Dict[str, FlightManifest]:
        for manifest in registry.values():
            if manifest.lifecycle in {FlightLifecycle.INTEGRATED, FlightLifecycle.ABANDONED}:
                continue
            if not manifest.is_heartbeat_expired(now):
                continue
            manifest.airspace = AirspaceStatus.STALE
            owner_alive = bool(
                self.owner_probe_callback and self.owner_probe_callback(manifest.session_id)
            )
            if owner_alive:
                manifest.refresh_heartbeat(now)
                manifest.airspace = AirspaceStatus.CLEAR
            else:
                manifest.lifecycle = FlightLifecycle.ABANDONED
        return registry
