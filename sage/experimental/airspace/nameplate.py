"""Canonical agent identity and progression nameplates for SAGE interfaces.

The nameplate is a read-only projection over canonical AirspaceState. It never
creates, promotes, or infers qualification. Rank/XP values come only from the
persisted progression state already maintained by the Airspace subsystem.

Milestone Strikes are likewise presentation-only: a validated upstream impact
level is rendered as earned stars. This module never decides whether an impact
is safe, validated, or promotion-worthy.
"""

from __future__ import annotations

from typing import Any

from sage.experimental.airspace.models import AirspaceState, StationID


STATION_ICONS = {
    StationID.MISSION_DIRECTOR: "◆",
    StationID.MISSION_CONTROL: "◈",
    StationID.INTEL_STATION: "◇",
    StationID.ENGINEERING_FLIGHT: "▣",
}

STATION_NAMEPLATES = {
    StationID.MISSION_DIRECTOR: "[SAGE::DIRECTOR]",
    StationID.MISSION_CONTROL: "[SAGE::C2::CHATGPT]",
    StationID.INTEL_STATION: "[SAGE::INTEL::GEMINI]",
    StationID.ENGINEERING_FLIGHT: "[SAGE::ENGINEER::JULES]",
}

MAX_MILESTONE_STRIKE_STARS = 5


def render_milestone_strike(stars: int) -> str:
    """Render an earned Milestone Strike from a validated impact level.

    ``stars`` must already be produced by the governed evidence/validation
    layer. This projection deliberately performs no scoring or qualification.
    Zero stars renders an explicit unearned state; one through five stars show
    increasing validated progress.
    """
    if not isinstance(stars, int) or isinstance(stars, bool):
        raise TypeError("milestone strike stars must be an integer")
    if not 0 <= stars <= MAX_MILESTONE_STRIKE_STARS:
        raise ValueError(
            f"milestone strike stars must be between 0 and {MAX_MILESTONE_STRIKE_STARS}"
        )
    earned = "⭐" * stars
    return f"MILESTONE STRIKE: {earned or '—'}"


def _display_xp(value: Any) -> Any:
    """Keep legacy integer-shaped projections while preserving fractional XP."""
    try:
        if value == value.to_integral_value():
            return int(value)
    except AttributeError:
        pass
    return value


def render_agent_nameplate(
    state: AirspaceState,
    station_id: StationID,
    *,
    compact: bool = True,
) -> str:
    """Render stable progression data from canonical state."""
    station = state.stations[station_id]
    xp = _display_xp(state.game_progression.get_total_xp_for_station(station_id))
    icon = STATION_ICONS.get(station_id, "▪")
    sql = f" SQL-{station.current_sql}" if station.current_sql > 0 else ""

    if compact:
        return f"{icon} {station.agent_name} // CQL-{station.current_cql}{sql} // XP {xp}"

    return (
        f"{icon} {station.agent_name}\n"
        f"  STATION : {station_id.value}\n"
        f"  CQL     : CQL-{station.current_cql}\n"
        f"  SQL     : SQL-{station.current_sql}\n"
        f"  XP      : {xp}"
    )


def render_chat_nameplate(state: AirspaceState, station_id: StationID) -> str:
    """Render the canonical identity token plus progression values."""
    return f"{STATION_NAMEPLATES[station_id]} {render_agent_nameplate(state, station_id)}"


def build_agent_identity(
    state: AirspaceState,
    station_id: StationID,
    *,
    state_label: str,
) -> dict[str, Any]:
    """Project identity, role, qualification, progression, and live state.

    This function is deliberately presentation-only. Every displayed value is
    sourced from canonical AirspaceState or the supplied read-only state
    projection; it cannot award XP, change qualification, or grant authority.
    """
    station = state.stations[station_id]
    return {
        "nameplate": STATION_NAMEPLATES[station_id],
        "station_id": station_id.value,
        "agent_name": station.agent_name,
        "role": station.role_description,
        "cql": station.current_cql,
        "sql": station.current_sql,
        "xp": _display_xp(state.game_progression.get_total_xp_for_station(station_id)),
        "state": state_label,
        "read_only": True,
        "authority": "canonical_airspace_state",
    }


def render_agent_identity(
    state: AirspaceState,
    station_id: StationID,
    *,
    state_label: str,
) -> str:
    """Render the human/agent HUD line from canonical identity and state."""
    identity = build_agent_identity(state, station_id, state_label=state_label)
    sql = f" • SQL-{identity['sql']}" if identity["sql"] > 0 else ""
    return (
        f"{identity['nameplate']} • CQL-{identity['cql']}{sql} • "
        f"XP {identity['xp']} • {identity['state']}"
    )
