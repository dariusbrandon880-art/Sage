"""Canonical agent identity and progression nameplates for SAGE interfaces.

The nameplate is a read-only projection over canonical AirspaceState. It never
creates, promotes, or infers qualification. Rank/XP values come only from the
persisted progression state already maintained by the Airspace subsystem.
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

RANK_TITLES = {
    StationID.MISSION_DIRECTOR: {
        0: "Director Candidate",
        4: "Mission Director",
        7: "Fleet Commander",
    },
    StationID.MISSION_CONTROL: {
        0: "Flight Controller Trainee",
        3: "C2 Flight Controller",
        7: "Chief C2 Strategist",
    },
    StationID.INTEL_STATION: {
        0: "Recon Analyst Trainee",
        3: "Senior Intel Specialist",
        7: "Chief Recon Officer",
    },
    StationID.ENGINEERING_FLIGHT: {
        0: "Junior Engineer",
        3: "Flight Engineer",
        4: "Senior Software Engineer",
        7: "Lead Systems Architect",
    },
}


def get_rank_title(station_id: StationID, cql_level: int) -> str:
    """Derive rank title from station responsibility and CQL qualification level."""
    titles = RANK_TITLES.get(station_id, {})
    matching_thresholds = [lvl for lvl in sorted(titles.keys()) if lvl <= cql_level]
    if matching_thresholds:
        return titles[matching_thresholds[-1]]
    return "Operational Agent"


def render_agent_nameplate(
    state: AirspaceState,
    station_id: StationID,
    *,
    compact: bool = True,
) -> str:
    """Render stable progression data from canonical state."""
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
        "xp": state.game_progression.get_total_xp_for_station(station_id),
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


def build_nametag_badge(
    state: AirspaceState,
    station_id: StationID,
    *,
    state_label: str = "OPERATIONAL",
) -> dict[str, Any]:
    """Build structured read-only nametag badge data payload."""
    station = state.stations[station_id]
    xp = state.game_progression.get_total_xp_for_station(station_id)
    rank_title = get_rank_title(station_id, station.current_cql)
    icon = STATION_ICONS.get(station_id, "▪")
    nameplate = STATION_NAMEPLATES[station_id]

    return {
        "nameplate": nameplate,
        "station_id": station_id.value,
        "agent_name": station.agent_name,
        "rank_title": rank_title,
        "icon": icon,
        "cql": station.current_cql,
        "sql": station.current_sql,
        "xp": xp,
        "state": state_label,
        "verification_badge": f"[VERIFIED::CQL-{station.current_cql}]",
        "read_only": True,
    }


def render_nametag_badge(
    state: AirspaceState,
    station_id: StationID,
    *,
    state_label: str = "OPERATIONAL",
) -> str:
    """Render single-line compact ASCII nametag badge for HUD/chat headers."""
    badge = build_nametag_badge(state, station_id, state_label=state_label)
    sql_str = f" • SQL-{badge['sql']}" if badge["sql"] > 0 else ""
    return (
        f"{badge['nameplate']} {badge['icon']} {badge['agent_name']} "
        f"({badge['rank_title']}) • CQL-{badge['cql']}{sql_str} • "
        f"XP {badge['xp']} • {badge['verification_badge']} • {badge['state']}"
    )
