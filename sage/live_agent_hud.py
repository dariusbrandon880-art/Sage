"""Live, read-only binding from canonical SAGE awareness to the agent HUD.

This closes the projection chain without introducing a new state system:
canonical Airspace/coordination readers -> awareness -> governed context -> HUD.
The binding is presentation-only and never authenticates, authorizes, mutates,
acknowledges, persists, or awards progression.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sage.agent_awareness import get_live_agent_awareness_snapshot
from sage.governed_context_view import build_governed_context_view

_AUDIENCE_BY_AGENT = {
    "MISSION_DIRECTOR": "SAGE::DIRECTOR",
    "MISSION_CONTROL": "SAGE::C2::CHATGPT",
    "INTEL_STATION": "SAGE::INTEL::GEMINI",
    "ENGINEERING_FLIGHT": "SAGE::ENGINEER::JULES",
}


def build_agent_hud_projection(context_view: dict[str, Any]) -> dict[str, Any]:
    """Project governed context view into shared presentation infrastructure."""
    if not isinstance(context_view, dict):
        raise TypeError("context_view must be a dictionary")
    if not context_view.get("bounded") or context_view.get("read_only") is not True:
        raise ValueError("HUD projection requires bounded, read-only context view")

    self_info = deepcopy(dict(context_view.get("self", {})))
    team_info = deepcopy(dict(context_view.get("team", {})))
    coord_info = deepcopy(dict(context_view.get("coordination", {})))

    roster = []
    for st_id, st_data in team_info.get("stations", {}).items():
        roster.append({
            "station_id": st_id,
            "nameplate": st_data.get("nameplate", f"[{st_id}]"),
            "agent_name": st_data.get("agent_name", st_id),
            "role": st_data.get("role", "Operator"),
            "cql": st_data.get("cql", 0),
            "sql": st_data.get("sql", 0),
            "xp": st_data.get("xp", 0),
            "state": st_data.get("state", "READY"),
        })

    pending = coord_info.get("pending", [])
    return {
        "context_id": context_view.get("context_id", "hud-context"),
        "audience": context_view.get("audience", "SAGE::C2::CHATGPT"),
        "presentation_only": True,
        "read_only": True,
        "self": {
            "nameplate": self_info.get("nameplate", "[SAGE::C2::CHATGPT]"),
            "agent_name": self_info.get("agent_name", "GPT"),
            "role": self_info.get("role", "Mission Control"),
            "cql": self_info.get("cql", 0),
            "sql": self_info.get("sql", 0),
            "xp": self_info.get("xp", 0),
            "state": self_info.get("state", "READY"),
        },
        "team": {
            "status": team_info.get("coordination", {}).get("status", "ACTIVE"),
            "roster": roster,
        },
        "coordination": {
            "pending_count": len(pending),
            "pending": pending,
            "delivery_semantics": coord_info.get("delivery_semantics", "pull_projection_only"),
        },
    }


def render_agent_hud(hud_projection: dict[str, Any]) -> str:
    """Render shared agent projection data as a compact internal surface."""
    if not isinstance(hud_projection, dict):
        raise TypeError("hud_projection must be a dictionary")

    self_info = hud_projection.get("self", {})
    team_info = hud_projection.get("team", {})
    coord_info = hud_projection.get("coordination", {})
    lines = [
        f"SELF: {self_info.get('nameplate')} CQL-{self_info.get('cql')}/SQL-{self_info.get('sql')} XP-{self_info.get('xp')} STATE={self_info.get('state')}",
    ]
    roster = team_info.get("roster", [])
    if roster:
        lines.append("TEAM: " + " ".join(f"{item.get('nameplate')}:{item.get('state')}" for item in roster))
    lines.append(f"COORDINATION: PENDING={coord_info.get('pending_count', 0)}")
    return "\n".join(lines)


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
    return build_agent_hud_projection(context_view=context)


def render_live_agent_hud(
    agent_id: str = "MISSION_CONTROL",
    *,
    context_id: str = "live-agent-hud",
    profile: str = "TEAM_COORDINATION",
    max_pending: int = 20,
) -> str:
    """Render the current governed shared projection without changing state."""
    return render_agent_hud(
        get_live_agent_hud(
            agent_id,
            context_id=context_id,
            profile=profile,
            max_pending=max_pending,
        )
    )