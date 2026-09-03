"""Canonical agent identity and progression nameplates for SAGE interfaces.

The nameplate is a read-only projection over canonical AirspaceState. It never
creates, promotes, or infers qualification. Rank/XP values come only from the
persisted progression state already maintained by the Airspace subsystem.

Milestone Strikes are presentation-only and are distinct from the locked Boss
badge/kill/capture model. Organism-wide Points and Boss state are available
through the manager-backed projection below so the display does not invent a
second source of truth.
"""

from __future__ import annotations

from typing import Any

from sage.experimental.airspace.boss_progression import BossProgressionAuthority
from sage.experimental.airspace.models import AirspaceState, StationID
from sage.experimental.airspace.organism_projection import OrganismProjection
from sage.experimental.airspace.points_xp_economy import PointsXPEconomy


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
    """Render an earned Milestone Strike from a validated impact level."""
    if not isinstance(stars, int) or isinstance(stars, bool):
        raise TypeError("milestone strike stars must be an integer")
    if not 0 <= stars <= MAX_MILESTONE_STRIKE_STARS:
        raise ValueError(
            f"milestone strike stars must be between 0 and {MAX_MILESTONE_STRIKE_STARS}"
        )
    earned = "⭐" * stars
    return f"MILESTONE STRIKE: {earned or '—'}"


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
    """Project identity, role, qualification, progression, and live state."""
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


def render_organism_nameplate(
    manager,
    station_id: StationID,
    *,
    compact: bool = True,
    state_label: str = "READY",
) -> str:
    """Render the full organism identity from canonical persisted state.

    This is the preferred progression-aware nameplate for operational use.
    Points and Boss outcomes are reconstructed from the same AirspaceManager
    ledger used by the canonical economy; no display-side state is created.
    """
    state = manager.reconstruct_airspace_state()
    projection = OrganismProjection.project_station(
        manager, state, station_id, status=state_label
    )
    boss = projection.boss
    identity = STATION_NAMEPLATES[station_id]
    icon = STATION_ICONS.get(station_id, "▪")
    sql = f" // SQL-{projection.sql}" if projection.sql > 0 else ""
    tag = (
        f"{identity} {icon} {projection.agent_name} // CQL-{projection.cql}{sql} // "
        f"POINTS {projection.points} // XP {projection.career_xp} // "
        f"BOSS ⭐×{boss.big_badges} ⭐⭐×{boss.major_badges} // "
        f"⚔️ {boss.total_kills} // ┃ {boss.total_captures} // {projection.status}"
    )
    if compact:
        return tag
    return (
        f"{tag}\n"
        f"  ROLE   : {projection.role}\n"
        f"  BADGES : {boss.badge_summary}\n"
        f"  BIG    : ⭐ | ⚔️ {boss.big_kills} | ┃ {boss.big_captures}\n"
        f"  MAJOR  : ⭐⭐ | ⚔️ {boss.major_kills} | ┃ {boss.major_captures}"
    )


def render_organism_roster(manager, *, state_label: str = "READY") -> str:
    """Render all canonical SAGE agents with one shared progression vocabulary."""
    state = manager.reconstruct_airspace_state()
    return OrganismProjection.render_roster(manager, state, status=state_label)
