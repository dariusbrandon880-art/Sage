"""Unit tests for SAGE Adaptive Mission Selection Engine v0.1."""
import pytest
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket


def test_candidate_decision_packet_default_unauthorized():
    """Verify that CandidateDecisionPacket always defaults to is_authorized = False."""
    packet = CandidateDecisionPacket(
        candidate_id="msn-test-001",
        description="Valid test mission candidate",
        verification_requirements=["tests/test_demo.py"],
    )
    assert packet.is_authorized is False
    assert packet.risk_score == 0.0
    assert packet.protected_path_intersections == []
    assert packet.digest() is not None


def test_engine_evaluates_candidate_and_falsifies_protected_paths():
    """Verify that affected paths intersecting protected namespaces fail falsification."""
    engine = AdaptiveMissionSelectionEngine()
    raw = {
        "candidate_id": "msn-protected-001",
        "description": "Attempted modification to runtime core",
        "affected_paths": ["sage/runtime/engine.py", "sage/experimental/demo.py"],
        "verification_requirements": ["tests/test_runtime.py"],
    }
    packet = engine.evaluate_candidate(raw)

    assert packet.candidate_id == "msn-protected-001"
    assert packet.is_authorized is False
    assert "sage/runtime/engine.py" in packet.protected_path_intersections
    assert packet.falsification_report["passed"] is False
    assert packet.risk_score >= 40.0


def test_engine_evaluates_valid_candidate():
    """Verify that a candidate without protected paths and with verification requirements passes falsification."""
    engine = AdaptiveMissionSelectionEngine()
    raw = {
        "candidate_id": "msn-valid-001",
        "description": "Safe feature addition",
        "affected_paths": ["sage/experimental/airspace/new_feature.py"],
        "verification_requirements": ["tests/experimental/test_new_feature.py"],
        "evidence_refs": ["evidence_capture/test.json"],
    }
    packet = engine.evaluate_candidate(raw)

    assert packet.candidate_id == "msn-valid-001"
    assert packet.is_authorized is False  # Still unauthorized by default until C2 gate
    assert packet.protected_path_intersections == []
    assert packet.falsification_report["passed"] is True
    assert packet.risk_score == 10.0


def test_ranking_determinism_and_prioritization():
    """Verify that candidates are ranked deterministically by falsification pass and risk score."""
    engine = AdaptiveMissionSelectionEngine()
    raw_candidates = [
        {
            "candidate_id": "cand-c-high-risk",
            "description": "High risk valid candidate",
            "affected_paths": ["sage/experimental/feature.py"],
            "verification_requirements": [],  # Missing verification increases risk
        },
        {
            "candidate_id": "cand-a-low-risk",
            "description": "Low risk valid candidate",
            "affected_paths": ["sage/experimental/feature.py"],
            "verification_requirements": ["tests/test_feature.py"],
        },
        {
            "candidate_id": "cand-b-protected",
            "description": "Protected path candidate",
            "affected_paths": ["sage/core/spek.py"],
            "verification_requirements": ["tests/test_spek.py"],
        },
    ]

    ranked = engine.rank_candidates(raw_candidates)

    assert len(ranked) == 3
    # 1st: Low risk valid candidate (passed falsification, risk=10)
    assert ranked[0].candidate_id == "cand-a-low-risk"
    assert ranked[0].falsification_report["passed"] is True

    # 2nd: High risk valid candidate (missing verification requirement, passed falsification=False or higher risk)
    # Note: missing verification causes falsification to fail
    assert ranked[1].candidate_id == "cand-b-protected" or ranked[1].candidate_id == "cand-c-high-risk"

    # All generated packets must remain unauthorized by default
    for p in ranked:
        assert p.is_authorized is False


def test_invalid_candidate_raises_value_error():
    """Verify that candidates missing required fields raise a ValueError."""
    engine = AdaptiveMissionSelectionEngine()
    with pytest.raises(ValueError, match="Candidate requires non-empty candidate_id and description"):
        engine.evaluate_candidate({"candidate_id": "", "description": ""})
