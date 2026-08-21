"""Governed coordination-event writer for SAGE's canonical Airspace ledger.

This is an observation/communication event surface, not an authority surface.
It records what an agent explicitly did or communicated; it cannot award XP,
promote qualification, authorize execution, or mutate mission/sortie state.
"""

from __future__ import annotations

import importlib
from datetime import datetime
from typing import Any


AGENT_COORDINATION_MESSAGE = "AGENT_COORDINATION_MESSAGE"
AGENT_HANDOFF = "AGENT_HANDOFF"
AGENT_ASSIGNMENT = "AGENT_ASSIGNMENT"
AGENT_CHALLENGE = "AGENT_CHALLENGE"
AGENT_VERIFICATION = "AGENT_VERIFICATION"
AGENT_COORDINATION_RECEIPT = "AGENT_COORDINATION_RECEIPT"

ALLOWED_COORDINATION_EVENT_TYPES = frozenset(
    {
        AGENT_COORDINATION_MESSAGE,
        AGENT_HANDOFF,
        AGENT_ASSIGNMENT,
        AGENT_CHALLENGE,
        AGENT_VERIFICATION,
        AGENT_COORDINATION_RECEIPT,
    }
)


def _recipients(event: dict[str, Any]) -> set[str]:
    payload = event.get("payload") or {}
    recipients = payload.get("recipients", payload.get("recipient", payload.get("to_agent")))
    if isinstance(recipients, str):
        return {recipients}
    if isinstance(recipients, list):
        return {str(value) for value in recipients}
    return set()


def _validate_receipt_payload(
    payload: dict[str, Any], *, actor: str, ledger_events: list[dict[str, Any]]
) -> None:
    allowed = {"acknowledged_event_id", "acknowledged_at"}
    if set(payload) != allowed:
        raise ValueError(
            "Receipt payload must contain exactly 'acknowledged_event_id' and 'acknowledged_at'"
        )
    acknowledged_event_id = payload["acknowledged_event_id"]
    acknowledged_at = payload["acknowledged_at"]
    if not isinstance(acknowledged_event_id, str) or not acknowledged_event_id.strip():
        raise ValueError("Receipt requires a non-empty acknowledged_event_id")
    if not isinstance(acknowledged_at, str) or not acknowledged_at.strip():
        raise ValueError("Receipt requires a non-empty acknowledged_at")
    try:
        datetime.fromisoformat(acknowledged_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Receipt acknowledged_at must be ISO-8601") from exc

    target = next(
        (event for event in ledger_events if event.get("event_id") == acknowledged_event_id),
        None,
    )
    if target is None:
        raise ValueError(f"Target event {acknowledged_event_id} does not exist in ledger")
    if actor not in _recipients(target):
        raise ValueError(
            f"Actor {actor} cannot acknowledge event intended for "
            f"{sorted(_recipients(target)) or 'no recipient'}"
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
    """Append one explicit coordination event to canonical Airspace state."""
    if event_type not in ALLOWED_COORDINATION_EVENT_TYPES:
        raise ValueError(f"Unsupported coordination event type: {event_type}")
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("Coordination event actor cannot be empty")
    if not isinstance(payload, dict):
        raise TypeError("Coordination event payload must be a dictionary")

    manager_module = importlib.import_module("sage.experimental.airspace.manager")
    manager = manager_module.AirspaceManager()
    if event_type == AGENT_COORDINATION_RECEIPT:
        _validate_receipt_payload(payload, actor=actor, ledger_events=manager._load_raw_events())

    event = manager.record_event(
        event_type=event_type,
        actor=actor,
        payload=payload,
        mission_id=mission_id,
        sortie_id=sortie_id,
        evidence_refs=evidence_refs or [],
    )
    return event.model_dump()
