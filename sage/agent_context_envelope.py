"""Transport-neutral, read-only SAGE Agent Context Envelope.

The envelope is a projection of canonical coordination and progression state.
It carries identity and delivery semantics without becoming an authority token
or changing the underlying event ledger.
"""

from __future__ import annotations

from typing import Any, Mapping


ENVELOPE_VERSION = "agent-context-envelope-v0.1"
PENDING = "PENDING"
ACKNOWLEDGED = "ACKNOWLEDGED"


def build_agent_context_envelope(
    *,
    sender: str,
    recipient: str,
    event_id: str,
    context_id: str | None,
    timestamp: str | None,
    event_type: str,
    payload: Mapping[str, Any],
    sender_identity_projection: Mapping[str, Any] | None,
    delivery_state: str = PENDING,
    authority: str = "canonical_airspace_state_and_event_ledger",
) -> dict[str, Any]:
    """Build a deterministic transport-neutral coordination envelope.

    This function is pure. It copies projection data and never writes to the
    Airspace ledger, progression state, qualification state, or mission state.
    """
    if delivery_state not in {PENDING, ACKNOWLEDGED}:
        raise ValueError(f"unsupported delivery_state: {delivery_state}")
    if not sender or not recipient or not event_id or not event_type:
        raise ValueError("sender, recipient, event_id, and event_type are required")

    identity = dict(sender_identity_projection) if sender_identity_projection else None
    return {
        "envelope_version": ENVELOPE_VERSION,
        "sender": sender,
        "recipient": recipient,
        "context_id": context_id,
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "projection_version": ENVELOPE_VERSION,
        "delivery_state": delivery_state,
        "delivery_semantics": "pull_projection_only",
        "sender_identity_projection": identity,
        "authority": authority,
        "read_only": True,
        "payload": dict(payload),
    }


def acknowledge_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Return an acknowledged projection without mutating the input."""
    if envelope.get("delivery_state") != PENDING:
        raise ValueError("only PENDING envelopes can transition to ACKNOWLEDGED")
    acknowledged = dict(envelope)
    acknowledged["delivery_state"] = ACKNOWLEDGED
    return acknowledged
