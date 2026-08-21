"""Read-only team coordination projection over canonical Airspace events.

Presence answers "who is here". Coordination answers "who is actually doing
what". Communication is only considered real when a corresponding canonical
Airspace event exists; UI presence alone never upgrades an agent to WORKING.

Unread coordination is a pure projection: it derives pending recipient events
from the append-only ledger and removes only events explicitly acknowledged by
a valid receipt. It never claims delivery, authority, or progression.
"""

from __future__ import annotations

import importlib
from typing import Any

from sage.coordination_events import AGENT_COORDINATION_RECEIPT


STANDBY = "STANDBY"
WORKING = "WORKING"
COORDINATING = "COORDINATING"
INTEL_CHALLENGE_ACTIVE = "INTEL_CHALLENGE_ACTIVE"
ENGINEERING_ACTIVE = "ENGINEERING_ACTIVE"
C2_REVIEW_ACTIVE = "C2_REVIEW_ACTIVE"
VERIFYING = "VERIFYING"

COORDINATION_EVENT_TYPES = {
    "MISSION_CREATED",
    "SORTIE_CREATED",
    "SORTIE_TRANSITIONED",
    "INTEL_RECORDED",
    "QUALIFICATION_PROMOTED",
    "QUALIFICATION_CHALLENGED",
    "XP_AWARDED",
    "AGENT_COORDINATION_MESSAGE",
    "AGENT_HANDOFF",
    "AGENT_ASSIGNMENT",
    "AGENT_CHALLENGE",
    "AGENT_VERIFICATION",
    AGENT_COORDINATION_RECEIPT,
}

DELIVERABLE_COORDINATION_EVENT_TYPES = {
    "AGENT_COORDINATION_MESSAGE",
    "AGENT_HANDOFF",
    "AGENT_ASSIGNMENT",
    "AGENT_CHALLENGE",
    "AGENT_VERIFICATION",
}


def _load() -> tuple[Any, Any]:
    manager_module = importlib.import_module("sage.experimental.airspace.manager")
    state = manager_module.AirspaceManager().reconstruct_airspace_state()
    return manager_module, state


def _events(manager_module: Any) -> list[dict[str, Any]]:
    manager = manager_module.AirspaceManager()
    return list(manager._load_raw_events())


def _recipients(event: dict[str, Any]) -> list[str]:
    payload = event.get("payload") or {}
    recipients = payload.get("recipients", payload.get("recipient", payload.get("to_agent")))
    if isinstance(recipients, str):
        return [recipients]
    return [str(value) for value in recipients] if isinstance(recipients, list) else []


def _active_sorties(state: Any) -> list[Any]:
    return [
        sortie
        for sortie in state.active_sorties
        if sortie.status.value in {"ACTIVE", "EVIDENCE_CAPTURE", "DEBRIEF"}
    ]


def _station_activity(station_id: Any, sorties: list[Any]) -> str:
    station_sorties = [s for s in sorties if s.station == station_id]
    if not station_sorties:
        return STANDBY
    current = station_sorties[-1]
    status = current.status.value
    if status in {"EVIDENCE_CAPTURE", "DEBRIEF"}:
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
    return STANDBY


def _communication_projection(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projected = []
    for event in events:
        payload = event.get("payload") or {}
        participants = payload.get("participants")
        if isinstance(participants, str):
            participants = [participants]
        if not isinstance(participants, list):
            participants = []
        projected.append(
            {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "timestamp": event.get("timestamp"),
                "actor": event.get("actor"),
                "recipients": _recipients(event),
                "participants": [str(v) for v in participants],
                "mission_id": event.get("mission_id"),
                "sortie_id": event.get("sortie_id"),
                "evidence_refs": list(event.get("evidence_refs", [])),
            }
        )
    return projected[-10:]


def _identity_for_actor(state: Any, actor: str) -> dict[str, Any] | None:
    """Resolve an event actor to canonical current identity without mutation."""
    models = importlib.import_module("sage.experimental.airspace.models")
    nameplate = importlib.import_module("sage.experimental.airspace.nameplate")
    coordination = importlib.import_module("sage.agent_coordination") if False else None
    _ = coordination  # Keep resolution independent of agent_presence imports.

    for station_id, station in state.stations.items():
        identity = nameplate.build_agent_identity(state, station_id, state_label=STANDBY)
        aliases = {
            station_id.value,
            station.agent_name,
            identity["nameplate"],
        }
        if actor in aliases:
            return identity
    return None


def get_unread_coordination(agent_id: str) -> list[dict[str, Any]]:
    """Return deterministic pending coordination events for one agent.

    This is strictly read-only. A returned event is *pending*, not claimed to
    have been delivered or received. Only an explicit canonical receipt removes
    it from the projection.
    """
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError("agent_id must be a non-empty string")

    manager_module, state = _load()
    events = _events(manager_module)
    acknowledged = {
        (event.get("payload") or {}).get("acknowledged_event_id")
        for event in events
        if event.get("event_type") == AGENT_COORDINATION_RECEIPT
        and event.get("actor") == agent_id
    }

    unread = []
    for event in events:
        event_id = event.get("event_id")
        if (
            event.get("event_type") not in DELIVERABLE_COORDINATION_EVENT_TYPES
            or agent_id not in _recipients(event)
            or event_id in acknowledged
        ):
            continue

        payload = event.get("payload") or {}
        sender_identity = _identity_for_actor(state, str(event.get("actor") or ""))
        unread.append(
            {
                "event_id": event_id,
                "event_type": event.get("event_type"),
                "timestamp": event.get("timestamp"),
                "actor": event.get("actor"),
                "recipients": _recipients(event),
                "mission_id": event.get("mission_id"),
                "sortie_id": event.get("sortie_id"),
                "evidence_refs": list(event.get("evidence_refs", [])),
                "payload": payload,
                "context_id": payload.get("context_id"),
                "sender_identity": sender_identity,
                "projection_version": "coordination-context-v0.1",
                "delivery_state": "PENDING",
                "delivery_semantics": "pull_projection_only",
                "read_only": True,
                "authority": "canonical_airspace_state_and_event_ledger",
            }
        )
    return unread


def get_coordination_state() -> dict[str, Any]:
    """Return deterministic, read-only team coordination state."""
    manager_module, state = _load()
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
            "mission_id": next((s.mission_id for s in sorties if s.station == station_id), None),
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
            "payload": e.get("payload") or {},
        }
        for e in events
        if e.get("event_type") in COORDINATION_EVENT_TYPES
    ]

    last_event = coordination_events[-1] if coordination_events else None
    if last_event:
        last_event = {k: v for k, v in last_event.items() if k != "payload"}

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
        "last_coordination_event": last_event,
        "recent_communications": _communication_projection(coordination_events),
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
