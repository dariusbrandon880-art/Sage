"""Pure projection of evaluated capability state into an Agent Context Envelope.

This module is non-authoritative: it consumes a verified CapabilityEvaluation
and an existing read-only envelope, then returns a new projection. It never
mutates capability registry, progression, authority, mission state, or storage.
"""

from __future__ import annotations

from typing import Any, Mapping

from sage.agent_context_envelope import ENVELOPE_VERSION
from sage.evidence_capability_evaluator import CapabilityEvaluation, EvidenceCapabilityEvaluator

PROJECTION_VERSION = "capability-projection-v0.1"


def project_capability_state(
    envelope: Mapping[str, Any],
    evaluation: CapabilityEvaluation,
) -> dict[str, Any]:
    """Return a new envelope with evidence-backed capability projection."""
    if not EvidenceCapabilityEvaluator.verify(evaluation):
        raise ValueError("capability evaluation integrity failed")
    if envelope.get("read_only") is not True:
        raise ValueError("capability projection requires a read-only envelope")
    if not envelope.get("context_id"):
        raise ValueError("envelope context_id is required")

    projected = dict(envelope)
    existing_identity = envelope.get("sender_identity_projection") or {}
    if not isinstance(existing_identity, Mapping):
        raise ValueError("sender_identity_projection must be a mapping")

    identity = dict(existing_identity)
    identity["capability_projection"] = {
        "projection_version": PROJECTION_VERSION,
        "evaluation_id": evaluation.evaluation_id,
        "evaluation_hash": evaluation.evaluation_hash,
        "capability_ref": evaluation.capability_ref,
        "verdict": evaluation.verdict,
        "capability_delta": evaluation.capability_delta,
        "reviewer_required": evaluation.reviewer_required,
        "authoritative": False,
    }
    projected["sender_identity_projection"] = identity
    projected["projection_version"] = ENVELOPE_VERSION
    projected["read_only"] = True
    return projected
