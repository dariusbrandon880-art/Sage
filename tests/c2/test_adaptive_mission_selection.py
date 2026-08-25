"""Tests for C2 Adaptive Mission Selection Engine."""

import pytest
from sage.c2.adaptive_mission_selection import (
    AdaptiveMissionSelectionEngine,
    CandidateDecisionPacket,
)


def test_candidate_decision_packet_hash_integrity():
    packet = CandidateDecisionPacket(
        candidate_id="cand-001",
        frontier_id="F1",
        target_namespace="sage/experimental/test",
        priority_score=0.9,
        is_authorized=True,
    )
    packet.decision_hash = packet.compute_hash()
    assert len(packet.decision_hash) == 64
    assert packet.decision_hash == packet.compute_hash()


def test_evaluate_candidate_unprotected_success():
    engine = AdaptiveMissionSelectionEngine()
    packet = engine.evaluate_candidate(
        candidate_id="cand-001",
        frontier_id="F1",
        target_namespace="sage/experimental/airspace",
    )
    assert packet.is_authorized is True
    assert packet.priority_score == 1.0
    assert packet.rejection_reason is None


def test_evaluate_candidate_protected_fails_without_token():
    engine = AdaptiveMissionSelectionEngine()
    packet = engine.evaluate_candidate(
        candidate_id="cand-002",
        frontier_id="F1",
        target_namespace="sage/core/spek.py",
    )
    assert packet.is_authorized is False
    assert packet.priority_score == 0.0
    assert "protected" in packet.rejection_reason.lower()


def test_evaluate_candidate_protected_succeeds_with_token():
    engine = AdaptiveMissionSelectionEngine()
    packet = engine.evaluate_candidate(
        candidate_id="cand-002",
        frontier_id="F1",
        target_namespace="sage/core/spek.py",
        auth_token="SAGE_SYSTEM_AUTH_TOKEN",
    )
    assert packet.is_authorized is True
    assert packet.priority_score == 1.0


def test_evaluate_candidate_failure_history_penalty():
    engine = AdaptiveMissionSelectionEngine()
    failures = [
        {"target_namespace": "sage/experimental/airspace", "frontier_id": "F1"},
        {"target_namespace": "sage/experimental/airspace", "frontier_id": "F1"},
        {"target_namespace": "sage/experimental/airspace", "frontier_id": "F1"},
    ]
    packet = engine.evaluate_candidate(
        candidate_id="cand-003",
        frontier_id="F1",
        target_namespace="sage/experimental/airspace",
        failure_history=failures,
    )
    assert packet.priority_score == 0.25
    assert packet.is_authorized is False
    assert "below minimum authorization threshold" in packet.rejection_reason


def test_rank_candidates_sorting():
    engine = AdaptiveMissionSelectionEngine()
    proposals = [
        {
            "candidate_id": "cand-low",
            "frontier_id": "F_LOW",
            "target_namespace": "sage/experimental/low",
        },
        {
            "candidate_id": "cand-protected",
            "frontier_id": "F_PROT",
            "target_namespace": "sage/core/protected",
        },
    ]
    ranked = engine.rank_candidates(proposals)
    assert len(ranked) == 2
    # cand-low should be first because cand-protected fails auth without token
    assert ranked[0].candidate_id == "cand-low"
    assert ranked[0].is_authorized is True
    assert ranked[1].candidate_id == "cand-protected"
    assert ranked[1].is_authorized is False
