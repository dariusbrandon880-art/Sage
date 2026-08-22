"""Live, read-only binding from canonical SAGE awareness to the agent HUD.

This closes the projection chain without introducing a new state system:
canonical Airspace/coordination readers -> awareness -> governed context -> HUD.
The binding is presentation-only and never authenticates, authorizes, mutates,
acknowledges, persists, or awards progression.
"""

from __future__ import annotations

from typing import Any

from sage.agent_awareness import get_live_agent_awareness_snapshot
from sage.agent_hud_projection import build_agent_hud_projection, render_agent_hud
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
