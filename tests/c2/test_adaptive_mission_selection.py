"""Test suite for Adaptive Mission Selection Engine."""

import pytest
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket


def test_adaptive_mission_selection_evaluation():
    engine = AdaptiveMissionSelectionEngine()
    pkt = engine.evaluate_candidate(
        candidate_id="CAN-001",
        title="Implement Lineage Recovery",
        target_namespace="sage/experimental/capability_lineage.py",
        impact_score=8.0
    )

    assert pkt.candidate_id == "CAN-001"
    assert pkt.is_protected_namespace is False
    assert pkt.is_authorized is False  # Fail-closed default
    assert pkt.risk_score < 0.5
    assert pkt.priority_score > 0
    assert pkt.packet_hash != ""


def test_adaptive_mission_selection_protected_boundary_block():
    engine = AdaptiveMissionSelectionEngine()
    pkt = engine.evaluate_candidate(
        candidate_id="CAN-CORE",
        title="Modify Core Runtime",
        target_namespace="sage/core/engine.py",
        impact_score=9.0
    )

    assert pkt.is_protected_namespace is True
    assert len(pkt.rejection_reasons) == 1
    assert "violates core protected boundary" in pkt.rejection_reasons[0]


def test_adaptive_mission_selection_ranking():
    engine = AdaptiveMissionSelectionEngine()
    p1 = engine.evaluate_candidate("CAN-1", "Task 1", "sage/experimental/a.py", impact_score=5.0)
    p2 = engine.evaluate_candidate("CAN-2", "Task 2", "sage/experimental/b.py", impact_score=9.0)
    p3 = engine.evaluate_candidate("CAN-3", "Core Task", "sage/runtime/b.py", impact_score=10.0)

    ranked = engine.rank_candidates([p1, p2, p3])
    assert len(ranked) == 2  # p3 filtered out due to protected namespace
    assert ranked[0].candidate_id == "CAN-2"  # Higher impact score
    assert ranked[1].candidate_id == "CAN-1"
