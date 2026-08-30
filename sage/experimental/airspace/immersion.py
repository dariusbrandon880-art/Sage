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
