"""Deterministic airspace classification, independent of flight lifecycle."""

from typing import Dict

from .models import AirspaceStatus, FlightLifecycle, FlightManifest


_TERMINAL = {FlightLifecycle.INTEGRATED, FlightLifecycle.ABANDONED}


def classify_candidate(
    candidate: FlightManifest,
    active_registry: Dict[str, FlightManifest],
    canonical_head_sha: str,
) -> AirspaceStatus:
    """Classify a candidate against known ownership and telemetry state."""
    for flight_id, active in active_registry.items():
        if flight_id == candidate.flight_id or active.lifecycle in _TERMINAL:
            continue
        if active.is_heartbeat_expired():
            return AirspaceStatus.STALE
        if candidate.ownership.files & active.ownership.files:
            if active.lifecycle == FlightLifecycle.ACTIVE:
                return AirspaceStatus.OCCUPIED
            if active.pr_number is not None:
                return AirspaceStatus.DEPENDENT
        if candidate.ownership.symbols & active.ownership.symbols:
            return AirspaceStatus.OCCUPIED
        if candidate.ownership.artifacts & active.ownership.artifacts:
            return AirspaceStatus.OCCUPIED
        if candidate.ownership.modules & active.ownership.modules:
            return AirspaceStatus.SHARED

    if candidate.base_sha != canonical_head_sha and not candidate.is_mergeable:
        return AirspaceStatus.STALE
    return AirspaceStatus.CLEAR
