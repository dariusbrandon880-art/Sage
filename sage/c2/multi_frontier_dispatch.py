"""C2 adapter for the canonical five-slot Big Jump Wave engine.

Flight slots are reusable execution capacity. C2 supplies the mission for each
slot; this adapter never assigns permanent capability ownership to F1-F5 and
never manufactures PASS receipts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec


@dataclass(frozen=True)
class FlightReceipt:
    flight_id: str
    mission_id: str
    frontier_name: str
    boundary_scope: str
    status: str
    commit_sha: str
    proof_type: str
    proof_data: Dict[str, Any]
    receipt_hash: str


@dataclass
class MultiFrontierDispatchReceipt:
    commit_sha: str
    flight_receipts: List[FlightReceipt]
    collision_count: int
    collisions_detected: List[str]
    wave_verdict: str
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_sha": self.commit_sha,
            "flight_receipts": [asdict(r) for r in self.flight_receipts],
            "collision_count": self.collision_count,
            "collisions_detected": self.collisions_detected,
            "wave_verdict": self.wave_verdict,
            "summary": self.summary,
        }


def compute_receipt_hash(flight_id: str, mission_id: str, boundary_scope: str, proof_type: str, commit_sha: str) -> str:
    """Hash actual receipt identity fields deterministically."""
    import hashlib
    payload = f"{flight_id}:{mission_id}:{boundary_scope}:{proof_type}:{commit_sha}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class MultiFrontierDispatcher:
    """Dispatch five explicitly assigned, independently reusable flight slots."""

    def __init__(
        self,
        commit_sha: Optional[str] = None,
        engine_factory: Callable[[], BuildJumpWaveEngine] | None = None,
    ) -> None:
        self.commit_sha = commit_sha
        self._engine_factory = engine_factory or (lambda: BuildJumpWaveEngine(max_workers=5))

    def dispatch_all(self, missions: List[FlightMissionSpec]) -> MultiFrontierDispatchReceipt:
        if len(missions) != 5:
            raise ValueError(f"Big Jump Wave requires exactly 5 assigned missions, got {len(missions)}")
        if len({mission.flight_id for mission in missions}) != 5:
            raise ValueError("Big Jump Wave requires five unique flight IDs")

        engine = self._engine_factory()
        package = engine.execute_wave(wave_id="multi-frontier-dispatch", missions=missions)
        expected_sha = self.commit_sha or engine.get_current_head_sha()
        mission_by_flight = {mission.flight_id: mission for mission in missions}
        collisions: List[str] = []
        if package.total_flights != 5:
            collisions.append(f"expected 5 flights, observed {package.total_flights}")

        receipts: List[FlightReceipt] = []
        for flight in package.flight_summaries:
            mission = mission_by_flight.get(flight.flight_id)
            if mission is None:
                collisions.append(f"unknown flight returned: {flight.flight_id}")
                continue
            sha_matches = flight.exact_head == expected_sha
            if not sha_matches:
                collisions.append(f"stale or mismatched flight commit SHA detected: {flight.flight_id}")
            actual_pass = (
                flight.execution_result == "PASS"
                and sha_matches
                and flight.completed_all_stages()
                and flight.blocker is None
            )
            receipts.append(
                FlightReceipt(
                    flight_id=flight.flight_id,
                    mission_id=flight.flight_id,
                    frontier_name=mission.frontier_name,
                    boundary_scope=mission.collision_zone,
                    status="PASS" if actual_pass else "FAIL",
                    commit_sha=flight.exact_head,
                    proof_type="governed_wave_execution_summary",
                    proof_data={
                        "target": flight.target,
                        "tests_passed": flight.tests_passed,
                        "evidence_ref": flight.evidence_ref,
                        "pr_or_change": flight.pr_or_change,
                        "lifecycle_milestones": [
                            {"stage": milestone.stage.value, "passed": milestone.passed, "evidence_ref": milestone.evidence_ref}
                            for milestone in flight.lifecycle_milestones
                        ],
                    },
                    receipt_hash=compute_receipt_hash(
                        flight.flight_id, flight.flight_id, mission.collision_zone,
                        "governed_wave_execution_summary", flight.exact_head,
                    ),
                )
            )

        wave_verdict = "PASS" if package.reconvergence_verdict == "PASS" and not collisions else "HOLD"
        return MultiFrontierDispatchReceipt(
            commit_sha=expected_sha,
            flight_receipts=receipts,
            collision_count=len(collisions),
            collisions_detected=collisions,
            wave_verdict=wave_verdict,
            summary={
                "total_flights": package.total_flights,
                "execution_mode": "concurrent",
                "max_workers": 5,
                "reconvergence_verdict": package.reconvergence_verdict,
                "successful_flights": package.successful_flights,
                "blocked_flights": package.blocked_flights,
                "advancement_matrix_20_cells": package.advancement_matrix_20_cells,
                "first_pass_verification_rate": package.first_pass_verification_rate,
                "synthetic_receipts": False,
                "source": "BuildJumpWaveEngine",
                "flight_assignment_model": "open_reusable_slots",
            },
        )
