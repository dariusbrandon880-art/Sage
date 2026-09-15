"""Live, read-only binding from canonical SAGE awareness to the agent HUD.

This closes the projection chain without introducing a new state system:
canonical Airspace/coordination readers -> awareness -> governed context -> HUD.
The binding is presentation-only and never authenticates, authorizes, mutates,
acknowledges, persists, or awards progression.
"""

from __future__ import annotations

import importlib
from typing import Any

from sage.agent_awareness import get_live_agent_awareness_snapshot
from sage.governed_context_view import build_governed_context_view

_AUDIENCE_BY_AGENT = {
    "MISSION_DIRECTOR": "SAGE::DIRECTOR",
    "MISSION_CONTROL": "SAGE::C2::CHATGPT",
    "INTEL_STATION": "SAGE::INTEL::GEMINI",
    "ENGINEERING_FLIGHT": "SAGE::ENGINEER::JULES",
}


def get_live_agent_hud(
    agent_id: str = "MISSION_CONTROL",
    *,
    context_id: str = "live-agent-hud",
    profile: str = "TEAM_COORDINATION",
    max_pending: int = 20,
) -> dict[str, Any]:
    """Project current canonical awareness through the governed HUD boundary."""
    awareness = get_live_agent_awareness_snapshot(agent_id)
    audience = _AUDIENCE_BY_AGENT.get(agent_id)
    if audience is None:
        raise ValueError(f"unsupported agent_id: {agent_id}")
    context = build_governed_context_view(
        awareness=awareness,
        audience=audience,
        purpose="HUD",
        context_id=context_id,
        profile=profile,
        max_pending=max_pending,
    )

    if context.get("bounded") is not True:
        raise ValueError("context source must be bounded")
    if context.get("read_only") is not True:
        raise ValueError("context source must be read-only")

    roster = []
    team_stations = context.get("team", {}).get("stations", {})
    for station_key, station_data in team_stations.items():
        roster.append(station_data)

    pending_coordination = context.get("coordination", {}).get("pending", [])

    return {
        "presentation_only": True,
        "read_only": context.get("read_only", True),
        "context_id": context.get("context_id", context_id),
        "audience": context.get("audience", audience),
        "purpose": context.get("purpose", "HUD"),
        "self": context.get("self", {}),
        "team": {
            "coordination_status": context.get("team", {}).get("coordination", {}).get("status", "ACTIVE"),
            "roster": roster,
        },
        "coordination": {
            "pending_count": len(pending_coordination),
            "pending": pending_coordination,
            "delivery_semantics": context.get("coordination", {}).get("delivery_semantics", "pull_projection_only"),
        },
    }


def render_live_agent_hud(
    agent_id: str = "MISSION_CONTROL",
    *,
    context_id: str = "live-agent-hud",
    profile: str = "TEAM_COORDINATION",
    max_pending: int = 20,
) -> str:
    """Render the current governed HUD without creating or changing state."""
    hud_dict = get_live_agent_hud(
        agent_id,
        context_id=context_id,
        profile=profile,
        max_pending=max_pending,
    )

    self_info = hud_dict.get("self", {})
    nameplate = self_info.get("nameplate", "")
    cql = self_info.get("cql", 0)
    sql = self_info.get("sql", 0)
    xp = self_info.get("xp", 0)
    state = self_info.get("state", "WORKING")

    roster = hud_dict.get("team", {}).get("roster", [])
    roster_lines = [
        f"{r.get('nameplate')}:{r.get('state')}" for r in roster if "nameplate" in r
    ]
    roster_str = " | ".join(roster_lines)

    pending_count = hud_dict.get("coordination", {}).get("pending_count", 0)

    parts = [
        f"{nameplate} • CQL-{cql}/SQL-{sql} XP-{xp} STATE={state}",
    ]
    if roster_str:
        parts.append(f"ROSTER: {roster_str}")
    parts.append(f"PENDING={pending_count}")

    return "\n".join(parts)
