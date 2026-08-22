"""Governed bridge from longitudinal evidence into SAGI cognitive state.

This module is deliberately one-way and non-authoritative: empirical receipts may
produce validated facts or forbidden regressions, but they never authorize a new
flight, mutate canonical qualification, or turn a HOLD into success.
"""
from __future__ import annotations

from dataclasses import dataclass

from sage.experimental.cognitive.state_schema import (
    CognitiveForbiddenRegression,
    CognitiveValidatedFact,
)
from sage.experimental.longitudinal_capability import (
    CapabilityEvaluationReceipt,
    CapabilityVerdict,
)


@dataclass(frozen=True)
class SAGIEvidenceFeedback:
    receipt_hash: str
    verdict: CapabilityVerdict
    validated_facts: tuple[CognitiveValidatedFact, ...]
    forbidden_regressions: tuple[CognitiveForbiddenRegression, ...]


def project_flight_evidence(
    receipt: CapabilityEvaluationReceipt,
) -> SAGIEvidenceFeedback:
    """Project an immutable empirical receipt into cognitive evidence.

    PASS becomes a bounded validated fact. HOLD records no capability fact.
    NEGATIVE_RESULT becomes durable forbidden-regression knowledge. The projection
    contains no next action and therefore cannot itself authorize execution.
    """
    receipt_hash = receipt.receipt_hash()
    if receipt.verdict is CapabilityVerdict.PASS:
        fact = CognitiveValidatedFact(
            fact_id=f"flight-evidence:{receipt_hash}",
            statement=(
                "Longitudinal capability receipt passed its locked evaluation plan; "
                "the result remains evidence, not execution authority."
            ),
            evidence_references=[receipt_hash, receipt.plan_hash],
            confidence_score=1.0,
        )
        return SAGIEvidenceFeedback(
            receipt_hash=receipt_hash,
            verdict=receipt.verdict,
            validated_facts=(fact,),
            forbidden_regressions=(),
        )

    if receipt.verdict is CapabilityVerdict.NEGATIVE_RESULT:
        regression = CognitiveForbiddenRegression(
            regression_id=f"flight-negative:{receipt_hash}",
            description=(
                "Observed longitudinal negative result must remain visible to future "
                "frontier selection; failed conditions cannot be relabeled as capability."
            ),
            restricted_actions=list(receipt.fail_closed_reasons),
            blocked_states=["CAPABILITY_QUALIFICATION"],
        )
        return SAGIEvidenceFeedback(
            receipt_hash=receipt_hash,
            verdict=receipt.verdict,
            validated_facts=(),
            forbidden_regressions=(regression,),
        )

    # HOLD and INDETERMINATE preserve uncertainty rather than manufacturing memory.
    return SAGIEvidenceFeedback(
        receipt_hash=receipt_hash,
        verdict=receipt.verdict,
        validated_facts=(),
        forbidden_regressions=(),
    )
