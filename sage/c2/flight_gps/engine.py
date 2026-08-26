"""Observer/recommender orchestration for Flight GPS v1.2."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .classifier import classify_candidate
from .models import (
    AirspaceStatus,
    FlightManifest,
    GPSClearanceReceipt,
    ObservabilityState,
    generate_clearance_receipt,
)
from .registry import FlightRegistry
from .wave_planner import WavePlanner


@dataclass
class DispatchSnapshot:
    """Immutable result of one observation/planning cycle."""

    observability: ObservabilityState
    airspace: Dict[str, AirspaceStatus]
    recommended: List[FlightManifest]
    clearances: Dict[str, GPSClearanceReceipt] = field(default_factory=dict)


class FlightGPS:
    """Read-only control-plane observer; it does not merge, rebase, or mutate Git."""

    def __init__(self, canonical_head_sha: str, registry: FlightRegistry | None = None) -> None:
        self.canonical_head_sha = canonical_head_sha
        self.registry = registry or FlightRegistry()
        self.planner = WavePlanner()

    def observe(
        self,
        candidates: Iterable[FlightManifest],
        observability: ObservabilityState = ObservabilityState.NOMINAL,
    ) -> DispatchSnapshot:
        candidate_list = list(candidates)
        active = self.registry.snapshot()
        airspace = {
            candidate.flight_id: classify_candidate(candidate, active, self.canonical_head_sha)
            for candidate in candidate_list
        }
        recommended = self.planner.plan(candidate_list, airspace, observability)

        clearances = {
            candidate.flight_id: generate_clearance_receipt(
                flight_id=candidate.flight_id,
                capability_target=candidate.capability_target,
                exact_head_sha=self.canonical_head_sha,
                airspace_status=airspace[candidate.flight_id],
                observability_state=observability,
            )
            for candidate in candidate_list
        }

        return DispatchSnapshot(
            observability=observability,
            airspace=airspace,
            recommended=recommended,
            clearances=clearances,
        )
