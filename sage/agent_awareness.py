"""Read-only shared agent awareness projection for SAGE interfaces.

This module composes already-canonical identity/progression and coordination
projections into one deterministic, transport-neutral snapshot. It is a
presentation/context boundary only: it cannot award XP, change qualification,
grant authority, acknowledge delivery, or mutate mission state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping


AWARENESS_VERSION = "agent-awareness-v0.1"
CANONICAL_AUTHORITY = "canonical_airspace_state_and_event_ledger"


def build_agent_awareness_snapshot(
    *,
    agent_id: str,
    identity: Mapping[str, Any],
    team_context: Mapping[str, Any],
    unread_coordination: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compose a deterministic read-only awareness snapshot for one agent.

    The snapshot deliberately exposes current identity/progression, team state,
    and pending coordination envelopes without claiming that a message was
    delivered or that any displayed state grants authority.
    """
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError("agent_id must be a non-empty string")
    if not isinstance(identity, Mapping):
        raise TypeError("identity must be a mapping")
    if not isinstance(team_context, Mapping):
        raise TypeError("team_context must be a mapping")
    if not isinstance(unread_coordination, list):
        raise TypeError("unread_coordination must be a list")

    return {
        "awareness_version": AWARENESS_VERSION,
        "agent_id": agent_id,
        "self": deepcopy(dict(identity)),
        "team": deepcopy(dict(team_context)),
        "coordination": {
            "pending": deepcopy([dict(event) for event in unread_coordination]),
            "delivery_semantics": "pull_projection_only",
        },
        "read_only": True,
        "authority": CANONICAL_AUTHORITY,
    }


def get_agent_awareness_snapshot(
    agent_id: str = "MISSION_CONTROL",
    *,
    identity_provider: Callable[[str], Mapping[str, Any]],
    team_provider: Callable[[], Mapping[str, Any]],
    unread_provider: Callable[[str], list[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Build awareness from canonical read-only providers.

    Providers are injected so the composition remains transport-neutral and
    independently testable while production callers can bind canonical SAGE
    Airspace/coordination projections.
    """
    return build_agent_awareness_snapshot(
        agent_id=agent_id,
        identity=identity_provider(agent_id),
        team_context=team_provider(),
        unread_coordination=unread_provider(agent_id),
    )
