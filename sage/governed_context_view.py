"""Governed read-only context projection over SAGE agent awareness.

This boundary answers what an audience may see, for whom, and why, without
becoming an authority token or changing canonical state. It deliberately sits
above awareness composition and below any transport/HUD adapter.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


CONTEXT_VIEW_VERSION = "governed-context-view-v0.1"
CANONICAL_AUTHORITY = "canonical_airspace_state_and_event_ledger"
ALLOWED_AUDIENCES = frozenset({
    "SAGE::DIRECTOR",
    "SAGE::C2::CHATGPT",
    "SAGE::INTEL::GEMINI",
    "SAGE::ENGINEER::JULES",
})
ALLOWED_PURPOSES = frozenset({"HUD", "COORDINATION", "VERIFICATION"})
ALLOWED_PROFILES = frozenset({"SELF", "TEAM", "TEAM_COORDINATION"})


def build_governed_context_view(
    *,
    awareness: Mapping[str, Any],
    audience: str,
    purpose: str,
    context_id: str,
    profile: str = "TEAM_COORDINATION",
    max_pending: int = 20,
) -> dict[str, Any]:
    """Project an explicit, bounded subset of a canonical awareness snapshot.

    The result is pure and read-only. It does not authenticate, authorize,
    acknowledge, deliver, promote, mutate progression, or persist anything.
    """
    if not isinstance(awareness, Mapping):
        raise TypeError("awareness must be a mapping")
    if audience not in ALLOWED_AUDIENCES:
        raise ValueError(f"unsupported audience: {audience}")
    if purpose not in ALLOWED_PURPOSES:
        raise ValueError(f"unsupported purpose: {purpose}")
    if profile not in ALLOWED_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    if not isinstance(context_id, str) or not context_id.strip():
        raise ValueError("context_id must be a non-empty string")
    if not isinstance(max_pending, int) or isinstance(max_pending, bool) or max_pending < 0:
        raise ValueError("max_pending must be a non-negative integer")
    if awareness.get("read_only") is not True:
        raise ValueError("awareness source must be read-only")
    if awareness.get("authority") != CANONICAL_AUTHORITY:
        raise ValueError("awareness source must declare canonical authority")

    self_view = deepcopy(dict(awareness.get("self") or {}))
    team_view = deepcopy(dict(awareness.get("team") or {}))
    coordination = dict(awareness.get("coordination") or {})
    pending = deepcopy(list(coordination.get("pending") or []))[:max_pending]

    if profile == "SELF":
        team_view = {}
        pending = []
    elif profile == "TEAM":
        pending = []

    return {
        "context_view_version": CONTEXT_VIEW_VERSION,
        "context_id": context_id,
        "audience": audience,
        "purpose": purpose,
        "profile": profile,
        "self": self_view,
        "team": team_view,
        "coordination": {
            "pending": pending,
            "delivery_semantics": "pull_projection_only",
        },
        "bounded": True,
        "read_only": True,
        "authority": CANONICAL_AUTHORITY,
    }
