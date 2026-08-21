"""Read-only projection of SAGE Airspace identity, progression, and state.

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
    """Render a compact roster using canonical coordination activity."""
    models = importlib.import_module("sage.experimental.airspace.models")
    coordination = importlib.import_module("sage.agent_coordination")
    state = load_airspace_state()
    context = coordination.get_coordination_state()
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

    roster = []
    for station_id in ordered:
        station = state.stations[station_id]
        xp = state.game_progression.get_total_xp_for_station(station_id)
        activity = context["stations"][station_id.value]["activity"]
        marker = "*" if activity != coordination.STANDBY else "-"
        roster.append(
            f"{marker}{labels[station_id]}:{station.agent_name} "
            f"CQL-{station.current_cql}/SQL-{station.current_sql} XP-{xp}"
        )

    return f"TEAM {context['status']} | " + " | ".join(roster)


def render_chat_identity(station_id_value: str = "MISSION_CONTROL") -> str:
    """Render canonical agent identity, progression, and current activity."""
    models = importlib.import_module("sage.experimental.airspace.models")
    nameplate_module = importlib.import_module("sage.experimental.airspace.nameplate")
    coordination = importlib.import_module("sage.agent_coordination")
    state = load_airspace_state()
    station_id = models.StationID(station_id_value)
    activity = coordination.get_coordination_state()["stations"][station_id.value]["activity"]
    return nameplate_module.render_agent_identity(
        state,
        station_id,
        state_label=activity,
    )


def get_agent_identity(station_id_value: str = "MISSION_CONTROL") -> dict[str, Any]:
    """Return canonical identity/progression/live-state context for one agent."""
    models = importlib.import_module("sage.experimental.airspace.models")
    nameplate_module = importlib.import_module("sage.experimental.airspace.nameplate")
    coordination = importlib.import_module("sage.agent_coordination")
    state = load_airspace_state()
    station_id = models.StationID(station_id_value)
    activity = coordination.get_coordination_state()["stations"][station_id.value]["activity"]
    return nameplate_module.build_agent_identity(
        state,
        station_id,
        state_label=activity,
    )


def get_team_context() -> dict[str, Any]:
    """Return structured read-only team state suitable for agent context injection."""
    coordination = importlib.import_module("sage.agent_coordination")
    nameplate_module = importlib.import_module("sage.experimental.airspace.nameplate")
    models = importlib.import_module("sage.experimental.airspace.models")
    state = load_airspace_state()
    StationID = models.StationID
    coordination_state = coordination.get_coordination_state()

    stations = {}
    for station_id, station in state.stations.items():
        identity = nameplate_module.build_agent_identity(
            state,
            station_id,
            state_label=coordination_state["stations"][station_id.value]["activity"],
        )
        stations[station_id.value] = identity

    return {
        "stations": stations,
        "coordination": coordination_state,
        "read_only": True,
        "authority": "canonical_airspace_state",
    }
