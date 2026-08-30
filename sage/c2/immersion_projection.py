"""Read-only immersion projections derived from verified C2 state.

Enforces strict one-way state architecture:
    CANONICAL STATE -> IMMERSION PROJECTION -> PRESENTATION / RESPONSE CONTRACT
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from sage.c2.immersion_state import ImmersionState, ExecutionPhase, TrustStatus, FlightStatus


@dataclass(frozen=True)
class ImpactStars:
    """Evidence-bound visual progression; never an authority or source of truth."""

    verified_cells: int
    stars: int
    rank: str


@dataclass(frozen=True)
class MilestoneStrike:
    """A presentation event projected from an already verified wave result."""

    wave_id: str
    verdict: str
    impact: ImpactStars


@dataclass(frozen=True)
class NameplateProjection:
    """Deterministic presentation nameplate projected from canonical ImmersionState."""

    station_tag: str
    header: str
    flight: str
    phase: str
    trust: str
    frontier: str

    def render(self) -> str:
        return (
            f"{self.station_tag}\n"
            f"{self.header}\n"
            f"FLIGHT: {self.flight}\n"
            f"PHASE: {self.phase}\n"
            f"TRUST: {self.trust}\n"
            f"FRONTIER: {self.frontier}"
        )


@dataclass(frozen=True)
class MissionHUDProjection:
    """Deterministic mission control HUD projected from canonical ImmersionState."""

    mission: str
    phase: str
    flight_id: str
    flight_status: str
    trust_status: str
    frontier: str
    gate: str
    evidence_summary: str
    next_move: str

    def render(self) -> str:
        return (
            "==================================================\n"
            "SAGE MISSION CONTROL HUD\n"
            "==================================================\n"
            f"MISSION  : {self.mission}\n"
            f"PHASE    : {self.phase}\n"
            f"FLIGHT   : {self.flight_id} ({self.flight_status})\n"
            f"TRUST    : {self.trust_status}\n"
            f"FRONTIER : {self.frontier}\n"
            f"GATE     : {self.gate}\n"
            f"EVIDENCE : {self.evidence_summary}\n"
            f"NEXT MOVE: {self.next_move}\n"
            "=================================================="
        )


@dataclass(frozen=True)
class C2ResponseContract:
    """Governed response container containing deterministic nameplate and HUD projections."""

    nameplate: NameplateProjection
    hud: MissionHUDProjection
    read_only: bool = True
    authority: str = "canonical_immersion_state"

    def render_full_envelope(self, content_body: str = "") -> str:
        parts = [self.nameplate.render(), "", self.hud.render()]
        if content_body and content_body.strip():
            parts.extend(["", content_body.strip()])
        return "\n".join(parts)


def project_impact_stars(*, verified_cells: int, total_cells: int, verdict: str) -> ImpactStars:
    """Project SAFE-impact stars from verified milestone cells only.

    A failed/unknown wave always projects zero stars. A passing wave earns one
    star per completed four-cell tier, capped at five. This is presentation
    state only; it cannot promote or authorize capabilities.
    """
    if verified_cells < 0 or total_cells < 0 or verified_cells > total_cells:
        raise ValueError("verified_cells must be between zero and total_cells")
    if verdict != "PASS":
        return ImpactStars(verified_cells=verified_cells, stars=0, rank="UNRANKED")
    stars = min(5, (verified_cells + 3) // 4)
    rank = ("UNRANKED", "QUALIFIED", "OPERATIONAL", "ADVANCED", "ELITE", "MASTER")[stars]
    return ImpactStars(verified_cells=verified_cells, stars=stars, rank=rank)


def project_milestone_strike(
    *, wave_id: str, reconvergence: Mapping[str, object], total_cells: int = 20
) -> MilestoneStrike:
    """Convert reconciled wave evidence into a safe visual milestone projection."""
    verdict = str(reconvergence.get("verdict", "HOLD"))
    verified = int(reconvergence.get("verified_cells", 0))
    return MilestoneStrike(
        wave_id=wave_id,
        verdict=verdict,
        impact=project_impact_stars(
            verified_cells=verified, total_cells=total_cells, verdict=verdict
        ),
    )


def project_immersion_nameplate(state: ImmersionState) -> NameplateProjection:
    """Project a deterministic presentation nameplate from canonical state."""
    if not state.validate():
        raise ValueError("Cannot project nameplate from invalid ImmersionState.")
    return NameplateProjection(
        station_tag=state.station_identity,
        header="MISSION CONTROL",
        flight=f"{state.flight_id} ({state.flight_status.value})",
        phase=state.phase.value,
        trust=state.trust_status.value,
        frontier=state.frontier,
    )


def project_mission_hud(state: ImmersionState) -> MissionHUDProjection:
    """Project a deterministic mission HUD from canonical state."""
    if not state.validate():
        raise ValueError("Cannot project mission HUD from invalid ImmersionState.")
    evidence_str = (
        f"{len(state.evidence_refs)} verified ref(s) [{', '.join(state.evidence_refs)}]"
        if state.evidence_refs
        else "NONE RECORDED"
    )
    return MissionHUDProjection(
        mission=state.mission,
        phase=state.phase.value,
        flight_id=state.flight_id,
        flight_status=state.flight_status.value,
        trust_status=state.trust_status.value,
        frontier=state.frontier,
        gate=state.gate,
        evidence_summary=evidence_str,
        next_move=state.next_move,
    )


def project_c2_response_contract(state: ImmersionState) -> C2ResponseContract:
    """Project the complete C2 Response Contract from canonical state."""
    nameplate = project_immersion_nameplate(state)
    hud = project_mission_hud(state)
    return C2ResponseContract(nameplate=nameplate, hud=hud)
