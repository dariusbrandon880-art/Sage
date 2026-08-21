"""Compact agent progression nameplates for SAGE conversational interfaces.

The nameplate is a presentation layer over canonical AirspaceState. It never
creates, promotes, or infers qualification. Rank/XP values come only from the
persisted progression state already maintained by the Airspace subsystem.
"""

from __future__ import annotations

from sage.experimental.airspace.models import AirspaceState, StationID


STATION_ICONS = {
    StationID.MISSION_DIRECTOR: "◆",
    StationID.MISSION_CONTROL: "◈",
    StationID.INTEL_STATION: "◇",
    StationID.ENGINEERING_FLIGHT: "▣",
}


def render_agent_nameplate(
    state: AirspaceState,
    station_id: StationID,
    *,
    compact: bool = True,
) -> str:
    """Render a stable, chat-friendly progression tag for one station.

    This is deliberately read-only. Qualification and XP are not awarded here;
    the nameplate merely exposes the already-validated state to the operator.
    """
    station = state.stations[station_id]
    xp = state.game_progression.get_total_xp_for_station(station_id)
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
    """Render the standard single-line nameplate for conversational output."""
    return f"[{render_agent_nameplate(state, station_id)}]"
