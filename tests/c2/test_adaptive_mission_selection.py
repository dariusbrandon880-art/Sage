"""Tests for C2 Adaptive Mission Selection Engine."""

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket


def test_decision_packet_hash_integrity():
    packet = CandidateDecisionPacket(candidate_id="cand-001", frontier_id="F1", target_namespace="sage/experimental/test", priority_score=0.9, is_authorized=True)
    packet.decision_hash = packet.compute_hash()
    assert len(packet.decision_hash) == 64
    assert packet.decision_hash == packet.compute_hash()


def test_unprotected_candidate_is_authorized():
    packet = AdaptiveMissionSelectionEngine().evaluate_candidate("cand-001", "F1", "sage/experimental/airspace")
    assert packet.is_authorized is True
    assert packet.priority_score == 1.0


def test_protected_candidate_requires_auth():
    engine = AdaptiveMissionSelectionEngine()
    rejected = engine.evaluate_candidate("cand-002", "F1", "sage/core/spek.py")
    assert rejected.is_authorized is False
    assert rejected.priority_score == 0.0
    accepted = engine.evaluate_candidate("cand-002", "F1", "sage/core/spek.py", auth_token="SAGE_SYSTEM_AUTH_TOKEN")
    assert accepted.is_authorized is True


def test_failure_history_can_close_authorization():
    failures = [{"target_namespace": "sage/experimental/airspace", "frontier_id": "F1"}] * 3
    packet = AdaptiveMissionSelectionEngine().evaluate_candidate("cand-003", "F1", "sage/experimental/airspace", failure_history=failures)
    assert packet.priority_score == 0.25
    assert packet.is_authorized is False


def test_rank_candidates_puts_authorized_first():
    ranked = AdaptiveMissionSelectionEngine().rank_candidates([
        {"candidate_id": "cand-low", "frontier_id": "F_LOW", "target_namespace": "sage/experimental/low"},
        {"candidate_id": "cand-protected", "frontier_id": "F_PROT", "target_namespace": "sage/core/protected"},
    ])
    assert [p.candidate_id for p in ranked] == ["cand-low", "cand-protected"]
