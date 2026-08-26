"""Observer/recommender orchestration for Flight GPS v1.2."""

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .classifier import classify_candidate
from .models import AirspaceStatus, FlightManifest, ObservabilityState
from .registry import FlightRegistry
from .wave_planner import WavePlanner


@dataclass
class DispatchSnapshot:
    """Immutable result of one observation/planning cycle."""

    observability: ObservabilityState
    airspace: Dict[str, AirspaceStatus]
    recommended: List[FlightManifest]


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
        return DispatchSnapshot(observability, airspace, recommended)
