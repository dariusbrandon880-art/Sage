"""Governed coordination-event writer for SAGE's canonical Airspace ledger.

This is an observation/communication event surface, not an authority surface.
It records what an agent explicitly did or communicated; it cannot award XP,
promote qualification, authorize execution, or mutate mission/sortie state.
"""

from __future__ import annotations

import importlib
from typing import Any


AGENT_COORDINATION_MESSAGE = "AGENT_COORDINATION_MESSAGE"
AGENT_HANDOFF = "AGENT_HANDOFF"
AGENT_ASSIGNMENT = "AGENT_ASSIGNMENT"
AGENT_CHALLENGE = "AGENT_CHALLENGE"
AGENT_VERIFICATION = "AGENT_VERIFICATION"

ALLOWED_COORDINATION_EVENT_TYPES = frozenset(
    {
        AGENT_COORDINATION_MESSAGE,
        AGENT_HANDOFF,
        AGENT_ASSIGNMENT,
        AGENT_CHALLENGE,
        AGENT_VERIFICATION,
    }
)


def record_coordination_event(
    *,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
    mission_id: str | None = None,
    sortie_id: str | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Append one explicit coordination event to canonical Airspace state.

    The writer is intentionally narrow. It accepts only communication and
    coordination observations; progression and authority remain separate APIs.
    """
    if event_type not in ALLOWED_COORDINATION_EVENT_TYPES:
        raise ValueError(f"Unsupported coordination event type: {event_type}")
    if not actor.strip():
        raise ValueError("Coordination event actor cannot be empty")
    if not isinstance(payload, dict):
        raise TypeError("Coordination event payload must be a dictionary")

    manager_module = importlib.import_module("sage.experimental.airspace.manager")
    event = manager_module.AirspaceManager().record_event(
        event_type=event_type,
        actor=actor,
        payload=payload,
        mission_id=mission_id,
        sortie_id=sortie_id,
        evidence_refs=evidence_refs or [],
    )
    return event.model_dump()
