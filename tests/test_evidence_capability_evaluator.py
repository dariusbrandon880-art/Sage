"""Adversarial tests for the evidence-to-capability evaluation boundary."""

import json

import pytest

from sage.decision_record import DecisionRecord, DecisionResolution
from sage.evidence_capability_evaluator import EvidenceCapabilityEvaluator


def make_decision() -> DecisionRecord:
    record = DecisionRecord(
        decision_id="decision-001",
        context_id="ctx-001",
        authority_ref="c2-level-1",
        evidence_refs=["receipt:001", "receipt:002"],
        decision_payload={"action": "evaluate", "target": "capability"},
        timestamp_locked="2026-08-21T23:00:00Z",
        active_authority_ref="c2-level-1",
    )
    record.add_resolution(
        DecisionResolution(
            resolution_id="resolution-001",
            verification_status="VERIFIED",
            ground_truth_result={"tests": "passed"},
            verified_timestamp="2026-08-21T23:05:00Z",
        )
    )
    return record


def test_complete_evidence_produces_promotion_candidate_not_promotion():
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"},
    )
    assert evaluation.verdict == "PROMOTION_CANDIDATE"
    assert evaluation.capability_delta == "CANDIDATE_UP"
    assert evaluation.reviewer_required is True
    assert not hasattr(evaluation, "grant_authority")
    assert not hasattr(evaluation, "promote")


def test_evaluator_does_not_mutate_decision():
    decision = make_decision()
    before = decision.serialize()
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        decision,
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"},
    )
    assert evaluation.decision_id == "decision-001"
    assert decision.serialize() == before


def test_missing_evidence_holds_closed():
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED"},
    )
    assert evaluation.verdict == "HOLD"
    assert evaluation.capability_delta == "NO_CHANGE"
    assert "PENDING:receipt:002" in evaluation.unmet_requirements


def test_falsified_evidence_holds_closed():
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "FALSIFIED", "receipt:002": "VERIFIED"},
    )
    assert evaluation.verdict == "HOLD"
    assert "FALSIFIED:receipt:001" in evaluation.unmet_requirements


def test_unbound_required_evidence_holds_closed():
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={
            "receipt:001": "VERIFIED",
            "receipt:002": "VERIFIED",
            "receipt:003": "VERIFIED",
        },
        required_evidence_refs=["receipt:001", "receipt:003"],
    )
    assert evaluation.verdict == "HOLD"
    assert "UNBOUND:receipt:003" in evaluation.unmet_requirements


def test_unresolved_decision_holds_closed():
    record = DecisionRecord(
        decision_id="decision-pending",
        context_id="ctx-001",
        authority_ref="c2-level-1",
        evidence_refs=["receipt:001"],
        decision_payload={"action": "evaluate"},
        timestamp_locked="2026-08-21T23:00:00Z",
        active_authority_ref="c2-level-1",
    )
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        record,
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED"},
    )
    assert evaluation.verdict == "HOLD"
    assert "NO_RESOLUTION" in evaluation.unmet_requirements


def test_falsified_resolution_holds_closed():
    record = DecisionRecord(
        decision_id="decision-false",
        context_id="ctx-001",
        authority_ref="c2-level-1",
        evidence_refs=["receipt:001"],
        decision_payload={"action": "evaluate"},
        timestamp_locked="2026-08-21T23:00:00Z",
        active_authority_ref="c2-level-1",
    )
    record.add_resolution(
        DecisionResolution(
            resolution_id="resolution-false",
            verification_status="FALSIFIED",
            ground_truth_result={"tests": "failed"},
            verified_timestamp="2026-08-21T23:05:00Z",
        )
    )
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        record,
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED"},
    )
    assert evaluation.verdict == "HOLD"
    assert "RESOLUTION:FALSIFIED" in evaluation.unmet_requirements


def test_deterministic_hash_and_replay():
    evaluator = EvidenceCapabilityEvaluator()
    a = evaluator.evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:002": "VERIFIED", "receipt:001": "VERIFIED"},
    )
    b = evaluator.evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"},
    )
    assert a.serialize() == b.serialize()
    assert evaluator.verify(a)
    assert json.loads(a.serialize())["reviewer_required"] is True


def test_tamper_detection():
    evaluation = EvidenceCapabilityEvaluator().evaluate(
        make_decision(),
        capability_ref="CAP-EXAMPLE",
        evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"},
    )
    payload = evaluation.to_dict()
    payload["verdict"] = "PROMOTED"
    tampered = evaluation.__class__(**payload)
    assert not EvidenceCapabilityEvaluator.verify(tampered)


def test_invalid_capability_reference_fails_closed():
    with pytest.raises(ValueError, match="capability_ref"):
        EvidenceCapabilityEvaluator().evaluate(
            make_decision(), capability_ref="", evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"}
        )


def test_invalid_decision_integrity_blocks_evaluation():
    record = make_decision()
    object.__setattr__(record, "_decision_hash", "0" * 64)
    with pytest.raises(ValueError, match="decision integrity failed"):
        EvidenceCapabilityEvaluator().evaluate(
            record,
            capability_ref="CAP-EXAMPLE",
            evidence_verdicts={"receipt:001": "VERIFIED", "receipt:002": "VERIFIED"},
        )
