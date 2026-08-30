"""Unified C2 immersion runtime projection.

This is the thin activation layer over canonical ImmersionState. It composes
existing nameplate/HUD/progression surfaces and exposes one deterministic,
read-only game-style frame. It never writes canonical state and never derives
authority from presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from sage.c2.immersion_projection import (
    C2ResponseContract,
    ImpactStars,
    MilestoneStrike,
    project_c2_response_contract,
    project_milestone_strike,
)
from sage.c2.immersion_state import ImmersionState


@dataclass(frozen=True)
class FlightCard:
    flight_id: str
    label: str
    status: str


@dataclass(frozen=True)
class ObservatoryProjection:
    mission: str
    station: str
    phase: str
    frontier: str
    flights: tuple[FlightCard, ...]
    evidence_refs: tuple[str, ...]
    next_gate: str
    next_move: str
    progression: ImpactStars
    render_mode: str = "SAGE_C2_IMMERSION"

    def render(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║ SAGE OBSERVATORY — C2 MISSION CONTROL          ║",
            "╠══════════════════════════════════════════════════╣",
            f"║ MISSION   {self.mission}",
            f"║ STATION   {self.station}",
            f"║ PHASE     {self.phase}",
            f"║ FRONTIER  {self.frontier}",
            "║",
            "║ ACTIVE FLIGHTS",
        ]
        for flight in self.flights:
            lines.append(f"║ {flight.flight_id:<4} {flight.label:<20} [{flight.status}]")
        lines.extend(
            [
                "║",
                f"║ EVIDENCE  {len(self.evidence_refs)} verified reference(s)",
                f"║ NEXT GATE {self.next_gate}",
                f"║ NEXT MOVE {self.next_move}",
                f"║ PROGRESS  {self.progression.stars}/5 SAFE-impact stars — {self.progression.rank}",
                "╚══════════════════════════════════════════════════╝",
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class ImmersionFrame:
    response: C2ResponseContract
    observatory: ObservatoryProjection
    milestone: MilestoneStrike | None

    @property
    def render_mode(self) -> str:
        return self.observatory.render_mode

    def render(self, content_body: str = "") -> str:
        parts = [self.response.render_full_envelope(content_body), "", self.observatory.render()]
        if self.milestone is not None:
            parts.extend(
                [
                    "",
                    f"MILESTONE STRIKE: {self.milestone.wave_id} — {self.milestone.verdict}",
                    f"SAFE IMPACT: {self.milestone.impact.stars}/5 — {self.milestone.impact.rank}",
                ]
            )
        return "\n".join(parts)


def activate_immersion(
    state: ImmersionState,
    *,
    flights: Sequence[Mapping[str, str]] = (),
    reconvergence: Mapping[str, object] | None = None,
    wave_id: str | None = None,
    total_cells: int = 20,
) -> ImmersionFrame:
    """Build the complete deterministic immersion frame from canonical state.

    ``state`` is the sole authority. Flight/progression inputs are projections
    of already-known evidence and are never written back into state.
    """
    if not state.validate():
        raise ValueError("Cannot activate immersion from invalid canonical state.")

    response = project_c2_response_contract(state)
    cards = tuple(
        FlightCard(
            flight_id=str(item.get("flight_id", "?")),
            label=str(item.get("label", "UNNAMED")),
            status=str(item.get("status", "UNKNOWN")),
        )
        for item in flights
    )
    progression = ImpactStars(verified_cells=0, stars=0, rank="UNRANKED")
    milestone = None
    if reconvergence is not None and wave_id:
        milestone = project_milestone_strike(
            wave_id=wave_id, reconvergence=reconvergence, total_cells=total_cells
        )
        progression = milestone.impact

    observatory = ObservatoryProjection(
        mission=state.mission,
        station=state.station_identity,
        phase=state.phase.value,
        frontier=state.frontier,
        flights=cards,
        evidence_refs=state.evidence_refs,
        next_gate=state.gate,
        next_move=state.next_move,
        progression=progression,
    )
    return ImmersionFrame(response=response, observatory=observatory, milestone=milestone)
