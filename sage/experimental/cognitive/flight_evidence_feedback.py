"""Bounded projection of empirical verdicts into cognitive learning candidates."""
from __future__ import annotations
from dataclasses import dataclass
from sage.experimental.cognitive.state_schema import CognitiveForbiddenRegression, CognitiveValidatedFact
from sage.experimental.longitudinal_capability import CapabilityEvaluationReceipt, CapabilityVerdict

@dataclass(frozen=True)
class SAGIEvidenceFeedback:
    receipt_hash: str
    verdict: CapabilityVerdict
    validated_facts: tuple[CognitiveValidatedFact, ...]
    forbidden_regressions: tuple[CognitiveForbiddenRegression, ...]

def project_flight_evidence(receipt: CapabilityEvaluationReceipt) -> SAGIEvidenceFeedback:
    receipt_hash = receipt.receipt_hash()
    if receipt.verdict is CapabilityVerdict.PASS:
        return SAGIEvidenceFeedback(receipt_hash, receipt.verdict, (CognitiveValidatedFact(
            fact_id=f"flight-evidence:{receipt_hash}", statement="Locked empirical receipt passed; evidence is not execution authority.",
            evidence_references=[receipt_hash, receipt.plan_hash], confidence_score=1.0),), ())
    if receipt.verdict is CapabilityVerdict.NEGATIVE_RESULT:
        return SAGIEvidenceFeedback(receipt_hash, receipt.verdict, (), (CognitiveForbiddenRegression(
            regression_id=f"flight-negative:{receipt_hash}", description="Observed negative result remains a forbidden regression constraint.",
            restricted_actions=list(receipt.fail_closed_reasons), blocked_states=["CAPABILITY_QUALIFICATION"]),))
    return SAGIEvidenceFeedback(receipt_hash, receipt.verdict, (), ())
