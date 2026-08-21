"""Read-only team coordination projection over canonical Airspace events.

This module does not create a second coordination store and never mutates
Airspace state. It derives human-readable and structured team activity from the
existing append-only Airspace ledger and reconstructed AirspaceState.

Presence answers "who is here". Coordination answers "who is actually doing
what". Communication is only considered real when a corresponding canonical
Airspace event exists; UI presence alone never upgrades an agent to WORKING.
"""

from __future__ import annotations

import importlib
from typing import Any


STANDBY = "STANDBY"
WORKING = "WORKING"
COORDINATING = "COORDINATING"
INTEL_CHALLENGE_ACTIVE = "INTEL_CHALLENGE_ACTIVE"
ENGINEERING_ACTIVE = "ENGINEERING_ACTIVE"
C2_REVIEW_ACTIVE = "C2_REVIEW_ACTIVE"
VERIFYING = "VERIFYING"

# Existing canonical Airspace event types. No new persistence channel is used.
COORDINATION_EVENT_TYPES = {
    "MISSION_CREATED",
    "SORTIE_CREATED",
    "SORTIE_TRANSITIONED",
    "INTEL_RECORDED",
    "QUALIFICATION_PROMOTED",
    "QUALIFICATION_CHALLENGED",
    "XP_AWARDED",
}


def _load() -> tuple[Any, Any, Any]:
    models = importlib.import_module("sage.experimental.airspace.models")
    manager_module = importlib.import_module("sage.experimental.airspace.manager")
    state = manager_module.AirspaceManager().reconstruct_airspace_state()
    return models, manager_module, state


def _events(manager_module: Any) -> list[dict[str, Any]]:
    """Read the canonical ledger through the existing manager's read path."""
    manager = manager_module.AirspaceManager()
    return list(manager._load_raw_events())


def _active_sorties(state: Any) -> list[Any]:
    return [
        sortie
        for sortie in state.active_sorties
        if sortie.status.value not in {"CLOSED", "ABORTED", "FAILED", "BLOCKED"}
    ]


def _station_activity(station_id: Any, sorties: list[Any]) -> str:
    station_sorties = [s for s in sorties if s.station == station_id]
    if not station_sorties:
        return STANDBY

    current = station_sorties[-1]
    status = current.status.value
    if status in {"EVIDENCE_CAPTURE", "DEBRIEF", "VERIFIED"}:
        return VERIFYING
    if status == "ACTIVE":
        value = station_id.value
        if value == "INTEL_STATION":
            return INTEL_CHALLENGE_ACTIVE
        if value == "ENGINEERING_FLIGHT":
            return ENGINEERING_ACTIVE
        if value == "MISSION_CONTROL":
            return C2_REVIEW_ACTIVE
        return WORKING
    if status in {"CLEARED", "BRIEFED", "CREATED"}:
        return WORKING
    return STANDBY


def get_coordination_state() -> dict[str, Any]:
    """Return deterministic, read-only team coordination state."""
    models, manager_module, state = _load()
    sorties = _active_sorties(state)
    stations = {}
    active_stations = []

    for station_id, station in state.stations.items():
        activity = _station_activity(station_id, sorties)
        if activity != STANDBY:
            active_stations.append(station_id.value)
        stations[station_id.value] = {
            "agent_name": station.agent_name,
            "activity": activity,
            "active": bool(activity != STANDBY and station.active_status),
            "mission_id": next(
                (s.mission_id for s in sorties if s.station == station_id), None
            ),
            "sorties": [s.sortie_id for s in sorties if s.station == station_id],
            "cql": station.current_cql,
            "sql": station.current_sql,
            "xp": state.game_progression.get_total_xp_for_station(station_id),
        }

    mission = state.active_mission
    assigned = [s.value for s in mission.assigned_stations] if mission else []
    overall = COORDINATING if len(set(active_stations)) > 1 else STANDBY
    if len(active_stations) == 1:
        overall = stations[active_stations[0]]["activity"]

    events = _events(manager_module)
    coordination_events = [
        {
            "event_id": e.get("event_id"),
            "event_type": e.get("event_type"),
            "timestamp": e.get("timestamp"),
            "actor": e.get("actor"),
            "mission_id": e.get("mission_id"),
            "sortie_id": e.get("sortie_id"),
            "evidence_refs": list(e.get("evidence_refs", [])),
        }
        for e in events
        if e.get("event_type") in COORDINATION_EVENT_TYPES
    ]

    return {
        "status": overall,
        "mission_id": mission.mission_id if mission else None,
        "mission_name": mission.mission_name if mission else None,
        "mission_objective": mission.objective if mission else None,
        "assigned_stations": assigned,
        "active_stations": active_stations,
        "stations": stations,
        "active_sorties": [
            {
                "sortie_id": s.sortie_id,
                "mission_id": s.mission_id,
                "station": s.station.value,
                "objective": s.objective,
                "status": s.status.value,
            }
            for s in sorties
        ],
        "last_coordination_event": coordination_events[-1] if coordination_events else None,
        "coordination_event_count": len(coordination_events),
        "read_only": True,
        "authority": "canonical_airspace_state_and_event_ledger",
    }


def render_coordination_status() -> str:
    """Render a compact truthful team activity line."""
    context = get_coordination_state()
    participants = []
    for station in context["stations"].values():
        if station["activity"] != STANDBY:
            participants.append(f"{station['agent_name']}:{station['activity']}")
    suffix = " | ".join(participants) if participants else "none"
    mission = context["mission_name"] or "no active mission"
    return f"TEAM {context['status']} | MISSION {mission} | ACTIVE {suffix}"
