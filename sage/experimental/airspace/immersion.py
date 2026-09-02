"""Read-only SAGE immersion projections.

This module adds the first implementation layer for the Immersion Language
Design Lab.  It deliberately consumes canonical AirspaceState and emits only
presentation data: symbols, stacks, tags, and live mission-state glyphs.

No function in this module awards XP, changes qualification, mutates missions,
or creates a second source of truth.  The casino-machine references are only
interaction-pattern inspiration; the rendered vocabulary remains SAGE
mission-control / aerospace / military language.
"""

from __future__ import annotations

from sage.experimental.airspace.models import AirspaceState, SortieState, StationID
from sage.experimental.airspace.nameplate import STATION_ICONS, STATION_NAMEPLATES


CAPABILITY_GLYPHS = {
    "CQL": "⚙️",
    "SQL": "🛰️",
}

SORTIE_GLYPHS = {
    SortieState.CREATED: "○",
    SortieState.BRIEFED: "▱",
    SortieState.CLEARED: "✓",
    SortieState.ACTIVE: "✈️",
    SortieState.EVIDENCE_CAPTURE: "🛡️",
    SortieState.DEBRIEF: "▣",
    SortieState.VERIFIED: "⭐",
    SortieState.CLOSED: "●",
    SortieState.BLOCKED: "⛔",
    SortieState.FAILED: "⚠️",
    SortieState.ABORTED: "↩",
}

SGP_RECOMMENDATION_GLYPHS = {
    "GRAVY": "🎰",
    "GENUINE_PLUS_EV": "📈",
    "BOOST_TRAP": "⚠️",
    "CONDITIONAL_ACCEPT": "🎯",
}

PICK_ACTION_GLYPHS = {
    "POSITIVE_EV": "📈",
    "EDGE": "⚡",
    "KELLY": "💰",
    "LOCKED": "🔒",
    "WIN": "🏆",
    "LOSS": "❌",
    "PUSH": "⏸️",
    "UNRESOLVED": "🎲",
}

CQL_LABELS = {
    0: "UNQUALIFIED",
    1: "CONCEPTUAL",
    2: "IMPLEMENTED",
    3: "VERIFIED",
    4: "OPERATIONAL",
    5: "CONTINUOUS",
    6: "ADAPTIVE",
    7: "FRONTIER",
}


def render_capability_stack(state: AirspaceState, station_id: StationID) -> str:
    """Render canonical CQL/SQL progression as a compact visual stack.

    One glyph represents each already-held qualification level.  This is the
    SAGE translation of stacked-symbol feedback: the stack is derived from
    canonical qualification state and cannot award anything itself.
    """
    station = state.stations[station_id]
    cql = max(0, min(7, station.current_cql))
    sql = max(0, min(7, station.current_sql))
    cql_stack = CAPABILITY_GLYPHS["CQL"] * cql or "—"
    sql_stack = CAPABILITY_GLYPHS["SQL"] * sql or "—"
    return f"CQL {cql_stack}  SQL {sql_stack}"


def render_capability_tags(state: AirspaceState, station_id: StationID) -> tuple[str, ...]:
    """Return persistent qualification tags derived from canonical levels."""
    station = state.stations[station_id]
    tags = []
    if station.current_cql > 0:
        tags.append(f"CQL-{station.current_cql} {CQL_LABELS[station.current_cql]}")
    if station.current_sql > 0:
        tags.append(f"SQL-{station.current_sql}")
    return tuple(tags)


def render_sortie_glyph(sortie_state: SortieState) -> str:
    """Render a mission-control glyph for a canonical sortie state."""
    return SORTIE_GLYPHS[sortie_state]


def render_live_sortie_strip(
    state: AirspaceState,
    *,
    station_id: StationID | None = None,
) -> str:
    """Render active sorties as compact live operational feedback."""
    sorties = state.active_sorties
    if station_id is not None:
        sorties = [sortie for sortie in sorties if sortie.station == station_id]
    if not sorties:
        return "NO ACTIVE SORTIES"
    return "  ".join(
        f"{render_sortie_glyph(sortie.status)} {sortie.station.value} {sortie.status.value}"
        for sortie in sorties
    )


def render_immersion_nameplate(
    state: AirspaceState,
    station_id: StationID,
    *,
    compact: bool = True,
) -> str:
    """Render a living nameplate using only canonical AirspaceState.

    The visual layer combines existing SAGE identity/progression with the new
    stacked-tag and live-sortie patterns.  It never persists or mutates state.
    """
    station = state.stations[station_id]
    xp = state.game_progression.get_total_xp_for_station(station_id)
    icon = STATION_ICONS.get(station_id, "▪")
    tags = render_capability_tags(state, station_id)
    stack = render_capability_stack(state, station_id)
    live = render_live_sortie_strip(state, station_id=station_id)
    identity = f"{STATION_NAMEPLATES[station_id]} {icon} {station.agent_name}"

    if compact:
        return (
            f"{identity} // CQL-{station.current_cql} // SQL-{station.current_sql} "
            f"// XP {xp} // {stack} // "
            f"{' | '.join(tags) if tags else 'UNQUALIFIED'} // {live}"
        )

    return (
        f"{identity}\n"
        f"  ROLE      : {station.role_description}\n"
        f"  XP        : {xp}\n"
        f"  STACK     : {stack}\n"
        f"  QUALIFIED : {' | '.join(tags) if tags else 'UNQUALIFIED'}\n"
        f"  SORTIES   : {live}"
    )


def render_station_operating_panel(
    state: AirspaceState,
    station_id: StationID,
    *,
    compact: bool = True,
) -> str:
    """Render the complete station-facing immersion panel.

    This is a composition-only surface: it exposes existing identity, XP,
    qualification, mission, frontier, evidence, clearance, and sortie state
    together without introducing new state or progression rules.
    """
    station = state.stations[station_id]
    xp = state.game_progression.get_total_xp_for_station(station_id)
    mission = state.active_mission
    mission_line = "NO ACTIVE MISSION"
    if mission is not None:
        mission_line = f"MISSION {mission.mission_id} // {mission.mission_name}"

    frontier = mission.current_frontier if mission is not None else "UNSPECIFIED"
    evidence_count = len(state.recent_evidence)
    tags = " | ".join(render_capability_tags(state, station_id)) or "UNQUALIFIED"
    live = render_live_sortie_strip(state, station_id=station_id)
    identity = f"{STATION_NAMEPLATES[station_id]} {STATION_ICONS.get(station_id, '▪')} {station.agent_name}"

    if compact:
        return (
            f"{identity} // XP {xp} // CQL-{station.current_cql} // SQL-{station.current_sql}\n"
            f"  {tags}\n"
            f"  {mission_line} // FRONTIER {frontier}\n"
            f"  EVIDENCE {evidence_count} // NEXT {state.next_clearance}\n"
            f"  {live}"
        )

    return (
        f"{identity}\n"
        f"  ROLE      : {station.role_description}\n"
        f"  XP        : {xp}\n"
        f"  STACK     : {render_capability_stack(state, station_id)}\n"
        f"  QUALIFIED : {tags}\n"
        f"  MISSION   : {mission_line}\n"
        f"  FRONTIER  : {frontier}\n"
        f"  EVIDENCE  : {evidence_count}\n"
        f"  NEXT      : {state.next_clearance}\n"
        f"  SORTIES   : {live}"
    )


def render_sgp_boost_glyph(recommendation: str) -> str:
    """Render a game immersion glyph for FanDuel SGP boost quality classification."""
    return SGP_RECOMMENDATION_GLYPHS.get(recommendation.upper(), "🎯")


def render_sports_pick_action_strip(
    *,
    player_or_selection: str,
    market_or_category: str,
    projected_prob: float,
    fd_price: float,
    expected_value: float,
    edge_score: float,
    kelly_stake: float,
    recommendation: str = "GENUINE_PLUS_EV",
    lock_verified: bool = True,
    outcome_status: str = "UNRESOLVED",
) -> str:
    """Render high-tempo sports pick visual action projection derived from canonical data.

    Visual feedback is read-only presentation derived from verified prediction state.
    It does not execute trades, place bets, or mutate underlying ledgers.
    """
    boost_glyph = render_sgp_boost_glyph(recommendation)
    ev_glyph = PICK_ACTION_GLYPHS["POSITIVE_EV"] if expected_value > 0 else "📉"
    lock_glyph = PICK_ACTION_GLYPHS["LOCKED"] if lock_verified else "🔓"

    outcome_glyph = {
        "WIN": PICK_ACTION_GLYPHS["WIN"],
        "LOSS": PICK_ACTION_GLYPHS["LOSS"],
        "PUSH": PICK_ACTION_GLYPHS["PUSH"],
    }.get(outcome_status.upper(), PICK_ACTION_GLYPHS["UNRESOLVED"])

    return (
        f"{boost_glyph} PICK [{player_or_selection} | {market_or_category}] "
        f"@ {fd_price:.2f} | PROB {projected_prob:.1%} | "
        f"EV {ev_glyph} {expected_value:+.2%} | "
        f"EDGE {PICK_ACTION_GLYPHS['EDGE']} {edge_score:+.2%} | "
        f"KELLY {PICK_ACTION_GLYPHS['KELLY']} {kelly_stake:.2%} | "
        f"LOCK {lock_glyph} | STATUS {outcome_glyph} {outcome_status}"
    )
