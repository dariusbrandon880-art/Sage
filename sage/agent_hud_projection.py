"""Human-readable, read-only HUD projection over governed SAGE context.

The HUD is an immersion/presentation surface, not a second state system. It
projects identity, progression, activity, and coordination state already
bounded by ``governed_context_view``. It cannot mutate authority, XP,
qualification, mission state, delivery state, or persistence.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


HUD_VERSION = "agent-hud-v0.1"


def build_agent_hud_projection(
    *,
    context_view: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic human/agent HUD projection from governed context."""
    if not isinstance(context_view, Mapping):
        raise TypeError("context_view must be a mapping")
    if context_view.get("bounded") is not True:
        raise ValueError("context source must be bounded")
    if context_view.get("read_only") is not True:
        raise ValueError("context source must be read-only")
    if not context_view.get("context_id"):
        raise ValueError("context source must declare context_id")

    self_view = deepcopy(dict(context_view.get("self") or {}))
    team_view = deepcopy(dict(context_view.get("team") or {}))
    coordination = deepcopy(dict(context_view.get("coordination") or {}))
    stations = deepcopy(dict(team_view.get("stations") or {}))

    roster = []
    for station_id, identity in stations.items():
        roster.append(
            {
                "station_id": station_id,
                "nameplate": identity.get("nameplate"),
                "agent_name": identity.get("agent_name"),
                "role": identity.get("role"),
                "cql": identity.get("cql"),
                "sql": identity.get("sql"),
                "xp": identity.get("xp"),
                "state": identity.get("state"),
            }
        )

    return {
        "hud_version": HUD_VERSION,
        "context_id": context_view["context_id"],
        "audience": context_view.get("audience"),
        "purpose": context_view.get("purpose"),
        "self": {
            "nameplate": self_view.get("nameplate"),
            "agent_name": self_view.get("agent_name"),
            "role": self_view.get("role"),
            "cql": self_view.get("cql"),
            "sql": self_view.get("sql"),
            "xp": self_view.get("xp"),
            "state": self_view.get("state"),
            "milestone_strike_stars": self_view.get("milestone_strike_stars", 0),
            "milestone_strike_label": self_view.get("milestone_strike_label", "UNRATED"),
        },
        "team": {
            "coordination_status": team_view.get("coordination", {}).get("status"),
            "roster": roster,
        },
        "coordination": {
            "pending_count": len(coordination.get("pending") or []),
            "pending": coordination.get("pending") or [],
            "delivery_semantics": coordination.get("delivery_semantics"),
        },
        "presentation_only": True,
        "read_only": True,
        "bounded": True,
    }


def render_agent_hud(projection: Mapping[str, Any]) -> str:
    """Render a compact SAGE HUD line without inventing state."""
    if not isinstance(projection, Mapping):
        raise TypeError("projection must be a mapping")
    self_view = projection.get("self") or {}
    team_view = projection.get("team") or {}
    roster = team_view.get("roster") or []
    pending = (projection.get("coordination") or {}).get("pending_count", 0)

    nameplate = self_view.get("nameplate") or "[SAGE::UNKNOWN]"
    cql = self_view.get("cql")
    sql = self_view.get("sql")
    xp = self_view.get("xp")
    state = self_view.get("state") or "UNKNOWN"
    roster_states = ", ".join(
        f"{item.get('nameplate')}:{item.get('state')}" for item in roster
    )

    return (
        f"{nameplate} CQL-{cql}/SQL-{sql} XP-{xp} STATE={state} | "
        f"TEAM={team_view.get('coordination_status')} | "
        f"PENDING={pending} | {roster_states}"
    )
