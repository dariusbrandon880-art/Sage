"""Live, read-only binding from canonical SAGE awareness to the agent HUD.

This closes the projection chain without introducing a new state system:
canonical Airspace/coordination readers -> awareness -> governed context -> HUD.
The binding is presentation-only and never authenticates, authorizes, mutates,
acknowledges, persists, or awards progression.
"""

from __future__ import annotations

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
    """Build a projection dict from a governed context view."""
    if not context_view.get("bounded"):
        raise ValueError("context view must be bounded")
    if not context_view.get("read_only"):
        raise ValueError("context view must be read-only")

    self_data = dict(context_view.get("self") or {})
    team_data = dict(context_view.get("team") or {})
    coordination = dict(context_view.get("coordination") or {})

    stations = dict(team_data.get("stations") or {})
    roster = list(stations.values())
    pending = list(coordination.get("pending") or [])

    return {
        "context_id": context_view.get("context_id"),
        "audience": context_view.get("audience"),
        "purpose": context_view.get("purpose"),
        "presentation_only": True,
        "read_only": True,
        "self": self_data,
        "team": {
            "coordination": team_data.get("coordination", {}),
            "roster": roster,
        },
        "coordination": {
            "pending_count": len(pending),
            "pending": pending,
        },
    }


def render_agent_hud(projection: dict[str, Any]) -> str:
    """Render a projection dict into a human-readable HUD string."""
    s = dict(projection.get("self") or {})
    cql = s.get("cql", 0)
    sql = s.get("sql", 0)
    xp = s.get("xp", 0)
    state = s.get("state", "UNKNOWN")
    nameplate = s.get("nameplate", "")

    team_roster = projection.get("team", {}).get("roster", [])
    team_str = " ".join(f"{st.get('nameplate', '')}:{st.get('state', '')}" for st in team_roster if isinstance(st, dict))
    pending_cnt = projection.get("coordination", {}).get("pending_count", 0)

    return f"{nameplate} CQL-{cql}/SQL-{sql} XP-{xp} STATE={state} | TEAM: {team_str} | PENDING={pending_cnt}".strip()


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
    """Render the current governed HUD without creating or changing state."""
    return render_agent_hud(
        get_live_agent_hud(
            agent_id,
            context_id=context_id,
            profile=profile,
            max_pending=max_pending,
        )
    )
