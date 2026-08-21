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
    context_id = envelope.get("context_id")
    if not context_id:
        raise ValueError("context_id is required for capability projection")

    decision_id = evaluation.decision_id
    # The evaluator's decision ID is the only linkage available here; the
    # projection must reject an envelope that cannot prove the same context.
    decision_context_id = getattr(evaluation, "context_id", None)
    if decision_context_id is not None and decision_context_id != context_id:
        raise ValueError("evaluation/envelope context mismatch")

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
    existing["projection_only"] = True
    projected["sender_identity_projection"] = existing
    projected["capability_projection_version"] = PROJECTION_VERSION
    projected["read_only"] = True
    return projected
