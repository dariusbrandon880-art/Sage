"""Unit and adversarial tests for SAGE C2 Adaptive Mission Selection Engine."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from sage.c2.adaptive_mission_selection import (
    AdaptiveMissionSelectionEngine,
    CandidateDecisionPacket,
)


def test_evaluate_candidate_authorized_with_token() -> None:
    engine = AdaptiveMissionSelectionEngine(commit_sha="commit_sha_999")
    packet = engine.evaluate_candidate(
        candidate_id="cand_test_001",
        proposal_title="Valid Experimental Proposal",
        target_lane="Lane 1",
        target_paths=["sage/experimental/test_module.py"],
        base_priority=1.5,
        c2_authorization_token="C2-AUTH-TOK-20260824-VALID",
    )

    assert packet.candidate_id == "cand_test_001"
    assert packet.is_authorized is True
    assert packet.requires_c2_token is False
    assert packet.protected_paths_touched == []
    assert packet.falsification_verdict == "VALIDATED_FEASIBLE"
    assert len(packet.provenance_hash) == 64


def test_evaluate_candidate_fails_closed_without_token() -> None:
    engine = AdaptiveMissionSelectionEngine(commit_sha="commit_sha_999")
    packet = engine.evaluate_candidate(
        candidate_id="cand_test_002",
        proposal_title="Proposal Without Token",
        target_lane="Lane 2",
        target_paths=["sage/experimental/test_module.py"],
        base_priority=1.0,
        c2_authorization_token=None,
    )

    assert packet.candidate_id == "cand_test_002"
    assert packet.is_authorized is False
    assert packet.requires_c2_token is True


def test_evaluate_candidate_falsified_on_protected_path() -> None:
    engine = AdaptiveMissionSelectionEngine(commit_sha="commit_sha_999")
    packet = engine.evaluate_candidate(
        candidate_id="cand_test_003",
        proposal_title="Proposal Touching Protected Core",
        target_lane="Protected Core",
        target_paths=["sage/core/engine.py"],
        base_priority=2.0,
        c2_authorization_token="C2-AUTH-TOK-20260824-PROTECTED",
    )

    assert packet.candidate_id == "cand_test_003"
    assert packet.is_authorized is False
    assert packet.protected_paths_touched == ["sage/core/engine.py"]
    assert packet.falsification_verdict == "FALSIFIED_REJECTED"


def test_select_and_rank_candidates() -> None:
    engine = AdaptiveMissionSelectionEngine(commit_sha="commit_sha_888")
    proposals = [
        {
            "candidate_id": "cand_low_priority",
            "proposal_title": "Low Priority Proposal",
            "target_lane": "Lane 1",
            "target_paths": ["sage/experimental/a.py"],
            "base_priority": 0.5,
        },
        {
            "candidate_id": "cand_high_priority",
            "proposal_title": "High Priority Proposal",
            "target_lane": "Lane 2",
            "target_paths": ["sage/experimental/b.py"],
            "base_priority": 1.8,
            "c2_authorization_token": "C2-AUTH-TOK-HIGH",
        },
    ]

    receipt = engine.select_and_rank_candidates(proposals)

    assert receipt.commit_sha == "commit_sha_888"
    assert receipt.total_candidates_evaluated == 2
    assert receipt.authorized_candidates_count == 1
    assert receipt.decision_packets[0].candidate_id == "cand_high_priority"
    assert receipt.decision_packets[1].candidate_id == "cand_low_priority"


def test_runner_script_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.execute_adaptive_mission_selection import main

    monkeypatch.setattr("scripts.execute_adaptive_mission_selection.REPO_ROOT", tmp_path)

    main()

    evidence_file = tmp_path / "evidence_capture" / "adaptive_mission_selection_evidence.json"
    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["selection_verdict"] == "GOVERNED_SELECTION_COMPLETE"
    assert data["total_candidates_evaluated"] == 4
    assert data["authorized_candidates_count"] == 2
