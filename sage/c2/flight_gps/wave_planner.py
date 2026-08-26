"""Dynamic five-slot Flight GPS wave planning."""

from typing import Iterable, List

from .models import AirspaceStatus, FlightManifest, ObservabilityState


class WavePlanner:
    """Observer-mode planner; it recommends safe candidates but performs no writes."""

    def plan(
        self,
        candidates: Iterable[FlightManifest],
        airspace: dict[str, AirspaceStatus],
        observability: ObservabilityState,
        max_slots: int = 5,
    ) -> List[FlightManifest]:
        if observability == ObservabilityState.OFFLINE:
            return []
        selected: List[FlightManifest] = []
        for candidate in candidates:
            status = airspace.get(candidate.flight_id, AirspaceStatus.OCCUPIED)
            if status not in {AirspaceStatus.CLEAR, AirspaceStatus.SHARED}:
                continue
            selected.append(candidate)
            if len(selected) == max_slots:
                break
        return selected
