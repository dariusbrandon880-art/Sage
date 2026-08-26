"""Tests for recovered C2 Adaptive Mission Selection Engine."""
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket

def test_candidate_decision_packet_hash_integrity():
    packet=CandidateDecisionPacket(candidate_id="cand-001",frontier_id="F1",target_namespace="sage/experimental/test",priority_score=.9,is_authorized=True); packet.decision_hash=packet.compute_hash(); assert len(packet.decision_hash)==64 and packet.decision_hash==packet.compute_hash()
def test_unprotected_candidate_authorized():
    p=AdaptiveMissionSelectionEngine().evaluate_candidate("c","F1","sage/experimental/airspace"); assert p.is_authorized and p.priority_score==1.0
def test_protected_candidate_requires_token():
    e=AdaptiveMissionSelectionEngine(); p=e.evaluate_candidate("c","F1","sage/core/x.py"); assert not p.is_authorized and p.priority_score==0.0; assert "protected" in p.rejection_reason.lower()
def test_protected_candidate_with_token():
    p=AdaptiveMissionSelectionEngine().evaluate_candidate("c","F1","sage/core/x.py",auth_token="SAGE_SYSTEM_AUTH_TOKEN"); assert p.is_authorized
def test_failure_history_penalizes_candidate():
    failures=[{"target_namespace":"sage/experimental/airspace","frontier_id":"F1"}]*3; p=AdaptiveMissionSelectionEngine().evaluate_candidate("c","F1","sage/experimental/airspace",failure_history=failures); assert p.priority_score==.25 and not p.is_authorized
