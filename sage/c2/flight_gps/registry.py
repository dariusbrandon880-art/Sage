"""In-memory registry for airborne Flight GPS manifests."""

from typing import Dict, Optional

from .models import FlightManifest


class FlightRegistry:
    """Small deterministic registry used by the observer/planner layer."""

    def __init__(self) -> None:
        self._flights: Dict[str, FlightManifest] = {}

    def register(self, manifest: FlightManifest) -> None:
        self._flights[manifest.flight_id] = manifest

    def get(self, flight_id: str) -> Optional[FlightManifest]:
        return self._flights.get(flight_id)

    def snapshot(self) -> Dict[str, FlightManifest]:
        return dict(self._flights)

    def remove(self, flight_id: str) -> None:
        self._flights.pop(flight_id, None)
