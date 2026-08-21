"""Pure projection of evaluated capability evidence into Agent Context Envelope state.

This module is intentionally non-authoritative: it creates a new envelope
projection from an already-verified capability evaluation. It never mutates
capability state, qualification, XP, authority, mission state, or persistence.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from sage.agent_context_envelope import ENVELOPE_VERSION
from sage.evidence_capability_evaluator import CapabilityEvaluation

PROJECTION_VERSION = "capability-context-projection-v0.1"


def project_capability_evaluation_to_envelope(
    envelope: Mapping[str, Any],
    evaluation: CapabilityEvaluation,
) -> dict[str, Any]:
    """Return a new envelope whose identity projection reflects verified evaluation.

    The projection is informational and review-gated. A promotion candidate is
    never converted into authority by this function. HOLD remains HOLD.
    """
    if not evaluation.verify(evaluation):
        raise ValueError("capability evaluation integrity failed")
    if envelope.get("envelope_version") != ENVELOPE_VERSION:
        raise ValueError("unsupported or missing Agent Context Envelope version")
    if not envelope.get("context_id"):
        raise ValueError("context_id is required for capability projection")

    projected = copy.deepcopy(dict(envelope))
    existing = copy.deepcopy(projected.get("sender_identity_projection") or {})
    existing["capability_projection_version"] = PROJECTION_VERSION
    existing["capability_evaluation_id"] = evaluation.evaluation_id
    existing["capability_ref"] = evaluation.capability_ref
    existing["capability_verdict"] = evaluation.verdict
    existing["capability_delta"] = evaluation.capability_delta
    existing["reviewer_required"] = evaluation.reviewer_required
    existing["evaluation_hash"] = evaluation.evaluation_hash
    existing["evaluation_version"] = evaluation.version
    existing["authority_granted"] = False
    existing["qualification_mutated"] = False
    projected["sender_identity_projection"] = existing
    projected["projection_version"] = PROJECTION_VERSION
    projected["read_only"] = True
    return projected
