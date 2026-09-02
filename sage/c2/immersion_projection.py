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
class PickActionProjection:
    """Read-only high-tempo pick/prediction visual projection derived from canonical state."""

    selection: str
    market: str
    decimal_price: float
    expected_value: float
    edge_score: float
    kelly_stake: float
    recommendation: str
    outcome_status: str

    def render(self) -> str:
        recommendation_glyph = {
            "GRAVY": "🎰",
            "GENUINE_PLUS_EV": "📈",
            "BOOST_TRAP": "⚠️",
            "CONDITIONAL_ACCEPT": "🎯",
        }.get(self.recommendation.upper(), "📈")

        ev_glyph = "📈" if self.expected_value > 0 else "📉"
        outcome_glyph = {
            "WIN": "🏆",
            "LOSS": "❌",
            "PUSH": "⏸️",
        }.get(self.outcome_status.upper(), "🎲")

        return (
            f"{recommendation_glyph} PICK [{self.selection} | {self.market}] "
            f"@ {self.decimal_price:.2f} | "
            f"EV {ev_glyph} {self.expected_value:+.2%} | "
            f"EDGE ⚡ {self.edge_score:+.2%} | "
            f"KELLY 💰 {self.kelly_stake:.2%} | "
            f"STATUS {outcome_glyph} {self.outcome_status}"
        )


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
class StrikeEvent:
    """Immutable micro-event in the high-tempo SAGE operational strike feed."""

    event_type: str  # e.g., "TARGET ACQUIRED", "STRIKE INBOUND", "HIT CONFIRMED", "EVIDENCE CAPTURED", "VERIFIED", "TARGET KILLED", "NEXT TARGET"
    glyph: str
    label: str
    detail: str = ""

    def render(self) -> str:
        if self.detail and self.detail.strip():
            return f"{self.glyph} {self.event_type} // {self.label}\n  {self.detail.strip()}"
        return f"{self.glyph} {self.event_type} // {self.label}"


@dataclass(frozen=True)
class StrikeFeedProjection:
    """Deterministic high-tempo strike feed projected from canonical operational events/state."""

    events: tuple[StrikeEvent, ...] = ()

    def render(self) -> str:
        if not self.events:
            return "⚡ STRIKE FEED // STANDBY"
        rendered_events = "\n".join(e.render() for e in self.events)
        return (
            "━" * 42 + "\n"
            "⚡ HIGH-TEMPO STRIKE FEED\n"
            "━" * 42 + "\n"
            f"{rendered_events}\n"
            "━" * 42
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
    strike_feed: StrikeFeedProjection | None = None

    def render(self) -> str:
        lines = [
            "==================================================",
            "01 — COMMAND BAND // SAGE MISSION CONTROL HUD",
            "==================================================",
            f"MISSION  : {self.mission}",
            f"PHASE    : {self.phase}",
            f"FLIGHT   : {self.flight_id} ({self.flight_status})",
            f"TRUST    : {self.trust_status}",
            f"FRONTIER : {self.frontier}",
            f"GATE     : {self.gate}",
            f"EVIDENCE : {self.evidence_summary}",
            f"NEXT MOVE: {self.next_move}",
            "==================================================",
        ]
        if self.strike_feed and self.strike_feed.events:
            lines.extend(["", "04 — STRIKE FEED", self.strike_feed.render()])
        return "\n".join(lines)


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


def project_strike_feed_from_state(state: ImmersionState) -> StrikeFeedProjection:
    """Project a high-tempo event strike feed deterministically from canonical state."""
    if not state.validate():
        raise ValueError("Cannot project strike feed from invalid ImmersionState.")

    events: list[StrikeEvent] = [
        StrikeEvent("TARGET ACQUIRED", "🎯", state.frontier, f"Gate: {state.gate}"),
        StrikeEvent("MARINE STRIKE", "⚡", f"Flight {state.flight_id}", f"Phase: {state.phase.value}"),
    ]

    if state.evidence_refs:
        events.append(
            StrikeEvent(
                "EVIDENCE CAPTURED",
                "🛡️",
                f"{len(state.evidence_refs)} Verified Ref(s)",
                ", ".join(state.evidence_refs),
            )
        )

    if state.trust_status == TrustStatus.VERIFIED:
        events.extend([
            StrikeEvent("HIT CONFIRMED", "✓", state.mission, f"Trust: {state.trust_status.value}"),
            StrikeEvent("TARGET KILLED", "◆", f"Frontier Seam Cleared", state.frontier),
        ])
    else:
        events.append(
            StrikeEvent("VERIFY IN PROGRESS", "⏳", f"Status: {state.trust_status.value}", state.next_move)
        )

    events.append(
        StrikeEvent("NEXT TARGET", "→", state.next_move, f"Provenance: {state.provenance_head or 'canonical_head'}")
    )

    return StrikeFeedProjection(events=tuple(events))


def project_mission_hud(
    state: ImmersionState,
    strike_feed: StrikeFeedProjection | None = None,
) -> MissionHUDProjection:
    """Project a deterministic mission HUD from canonical state."""
    if not state.validate():
        raise ValueError("Cannot project mission HUD from invalid ImmersionState.")
    evidence_str = (
        f"{len(state.evidence_refs)} verified ref(s) [{', '.join(state.evidence_refs)}]"
        if state.evidence_refs
        else "NONE RECORDED"
    )
    if strike_feed is None:
        strike_feed = project_strike_feed_from_state(state)

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
        strike_feed=strike_feed,
    )


def project_c2_response_contract(
    state: ImmersionState,
    strike_feed: StrikeFeedProjection | None = None,
) -> C2ResponseContract:
    """Project the complete C2 Response Contract from canonical state."""
    nameplate = project_immersion_nameplate(state)
    hud = project_mission_hud(state, strike_feed=strike_feed)
    return C2ResponseContract(nameplate=nameplate, hud=hud)


def project_pick_action_visual(
    *,
    selection: str,
    market: str,
    decimal_price: float,
    expected_value: float,
    edge_score: float,
    kelly_stake: float,
    recommendation: str = "GENUINE_PLUS_EV",
    outcome_status: str = "UNRESOLVED",
) -> PickActionProjection:
    """Project a high-tempo sports pick visual action projection derived from canonical data."""
    return PickActionProjection(
        selection=selection,
        market=market,
        decimal_price=decimal_price,
        expected_value=expected_value,
        edge_score=edge_score,
        kelly_stake=kelly_stake,
        recommendation=recommendation,
        outcome_status=outcome_status,
    )
