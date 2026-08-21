"""Read-only projection of SAGE Airspace progression for production interfaces.

This adapter deliberately exposes canonical Airspace state without making the
production CLI statically depend on the experimental Airspace namespace. It is
presentation/context plumbing only: it never awards XP, changes qualification,
or mutates Airspace state.
"""

from __future__ import annotations

import importlib
from typing import Any


def load_airspace_state() -> Any:
    """Reconstruct canonical Airspace state through the existing manager."""
    manager_module = importlib.import_module("sage.experimental.airspace.manager")
    return manager_module.AirspaceManager().reconstruct_airspace_state()


def render_team_status() -> str:
    """Render a compact roster showing all station ranks and current coordination."""
    models = importlib.import_module("sage.experimental.airspace.models")
    state = load_airspace_state()
    StationID = models.StationID

    ordered = (
        StationID.MISSION_DIRECTOR,
        StationID.MISSION_CONTROL,
        StationID.INTEL_STATION,
        StationID.ENGINEERING_FLIGHT,
    )
    labels = {
        StationID.MISSION_DIRECTOR: "Director",
        StationID.MISSION_CONTROL: "C2",
        StationID.INTEL_STATION: "Intel",
        StationID.ENGINEERING_FLIGHT: "Engineering",
    }

    active_mission = state.active_mission
    assigned = set(active_mission.assigned_stations) if active_mission else set()
    active_sorties = [s for s in state.active_sorties if s.status.value == "ACTIVE"]
    coordinating = len(assigned) > 1 or len(active_sorties) > 1
    activity = "COORDINATING" if coordinating else "STANDBY"

    roster = []
    for station_id in ordered:
        station = state.stations[station_id]
        xp = state.game_progression.get_total_xp_for_station(station_id)
        marker = "*" if station_id in assigned else "-"
        roster.append(
            f"{marker}{labels[station_id]}:{station.agent_name} "
            f"CQL-{station.current_cql}/SQL-{station.current_sql} XP-{xp}"
        )

    return f"TEAM {activity} | " + " | ".join(roster)


def render_chat_identity(station_id_value: str = "MISSION_CONTROL") -> str:
    """Render the active station nameplate plus shared team state."""
    models = importlib.import_module("sage.experimental.airspace.models")
    nameplate_module = importlib.import_module("sage.experimental.airspace.nameplate")
    state = load_airspace_state()
    station_id = models.StationID(station_id_value)
    return f"[{nameplate_module.render_agent_nameplate(state, station_id)}] {render_team_status()}"


def get_team_context() -> dict[str, Any]:
    """Return structured read-only team state suitable for agent context injection."""
    models = importlib.import_module("sage.experimental.airspace.models")
    state = load_airspace_state()
    StationID = models.StationID

    stations = {}
    for station_id, station in state.stations.items():
        stations[station_id.value] = {
            "agent_name": station.agent_name,
            "role": station.role_description,
            "cql": station.current_cql,
            "sql": station.current_sql,
            "xp": state.game_progression.get_total_xp_for_station(station_id),
            "active": station.active_status,
        }

    mission = state.active_mission
    return {
        "stations": stations,
        "coordination": {
            "status": "COORDINATING"
            if mission and len(mission.assigned_stations) > 1
            else "STANDBY",
            "mission_id": mission.mission_id if mission else None,
            "assigned_stations": [s.value for s in mission.assigned_stations] if mission else [],
            "active_sorties": [s.sortie_id for s in state.active_sorties if s.status.value == "ACTIVE"],
        },
        "read_only": True,
        "authority": "canonical_airspace_state",
    }
