"""Unit tests for SAGE C2 Frontier Admission Engine & Classification Ledger."""

import pytest
from sage.c2.frontier_admission import (
    FrontierAdmissionEngine,
    FrontierCandidate,
    FrontierState,
)


def test_frontier_admission_successful_evaluation():
    engine = FrontierAdmissionEngine()
    candidate = FrontierCandidate(
        frontier_id="F1-GOV-001",
        target="sage/c2/frontier_admission.py",
        source="C2 Directive",
        state=FrontierState.UNSTARTED,
        base_sha="407f7b52b161c520688bd8eef509146d86717c74",
        dependencies=[],
        collision_zone="sage/c2/frontier_admission.py",
        evidence_required=["tests/c2/test_frontier_admission.py"],
        stop_condition="All tests pass",
    )

    receipt = engine.classify_and_evaluate(candidate)

    assert receipt.admitted is True
    assert receipt.classified_state == FrontierState.ACTIVE
    assert receipt.collision_detected is False
    assert len(receipt.receipt_hash) == 64
    assert candidate.frontier_id in engine.active_frontiers


def test_frontier_admission_collision_rejection():
    engine = FrontierAdmissionEngine()

    candidate1 = FrontierCandidate(
        frontier_id="F1-001",
        target="target_a.py",
        source="C2",
        state=FrontierState.UNSTARTED,
        base_sha="sha123",
        collision_zone="sage/c2/shared_file.py",
        stop_condition="Pass",
    )

    candidate2 = FrontierCandidate(
        frontier_id="F2-002",
        target="target_b.py",
        source="C2",
        state=FrontierState.UNSTARTED,
        base_sha="sha123",
        collision_zone="sage/c2/shared_file.py",
        stop_condition="Pass",
    )

    receipt1 = engine.classify_and_evaluate(candidate1)
    assert receipt1.admitted is True

    receipt2 = engine.classify_and_evaluate(candidate2)
    assert receipt2.admitted is False
    assert receipt2.collision_detected is True
    assert receipt2.classified_state == FrontierState.RECONCILE
    assert "Collision detected" in receipt2.rejection_reason


def test_frontier_admission_superseded_rejection():
    engine = FrontierAdmissionEngine()

    candidate = FrontierCandidate(
        frontier_id="F3-OLD",
        target="old_target.py",
        source="C2",
        state=FrontierState.SUPERSEDED,
        base_sha="sha123",
        collision_zone="sage/c2/old_target.py",
        stop_condition="Pass",
    )

    receipt = engine.classify_and_evaluate(candidate)
    assert receipt.admitted is False
    assert receipt.classified_state == FrontierState.SUPERSEDED
    assert "cannot be admitted" in receipt.rejection_reason
