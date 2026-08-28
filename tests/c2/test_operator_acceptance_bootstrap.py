import json
import pytest
from sage.c2.operator_acceptance_bootstrap import BootstrapFailure, OperatorAcceptanceBootstrap

VALID_SHA = "a" * 40


def fake_git(*args):
    assert args == ("rev-parse", "HEAD")
    return VALID_SHA


def test_cold_start_rehydrates_and_locks_execution(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: (["PR #286"], ["Issue #901"]))
    state = b.rehydrate("mission-001", ["complete main mission"], ["side goal"], ["F1", "F2"])
    b.require_execution_ready(state)
    assert state.canonical_git_sha == VALID_SHA
    assert state.active_prs == ["PR #286"] and state.active_issues == ["Issue #901"]
    assert state.deterministic_gate.status == "PASS"
    assert state.deterministic_gate.checks["live_state_reconciled"] is True
    assert state.empirical_gate.status == "PENDING"


def test_operator_failure_elevates_defect_and_blocks_acceptance(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: ([], []))
    state = b.rehydrate("mission-002", ["goal"], [], ["F1"])
    b.capture_operator_observation(state, "chatgpt", "FAIL", "evidence://ops-001", "C2-OPS-001")
    assert state.empirical_gate.status == "FAIL"
    assert state.acceptance_status == "NOT_ACCEPTED"
    assert "C2-OPS-001" in state.open_defects


def test_operator_pass_requires_evidence_and_produces_receipt(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: ([], []))
    state = b.rehydrate("mission-003", ["goal"], [], ["F1"])
    b.capture_operator_observation(state, "gemini", "PASS", "evidence://ops-pass")
    receipt = b.evidence_receipt(state, tmp_path / "receipt.json")
    data = json.loads(receipt.read_text())
    assert state.acceptance_status == "ACCEPTED"
    assert data["receipt_hash"]


def test_cold_start_drift_fails_closed_on_invalid_head(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=lambda *args: "bad-head", state_provider=lambda: ([], []))
    with pytest.raises(BootstrapFailure, match="40-character SHA"):
        b.rehydrate("mission-004", ["goal"], [], [])


def test_missing_operator_evidence_fails_closed(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: ([], []))
    state = b.rehydrate("mission-005", ["goal"], [], [])
    with pytest.raises(BootstrapFailure, match="interface and evidence_ref"):
        b.capture_operator_observation(state, "", "PASS", "")


def test_live_state_provider_failure_fails_closed(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: (_ for _ in ()).throw(RuntimeError("connector down")))
    with pytest.raises(BootstrapFailure, match="unable to reconcile live state"):
        b.rehydrate("mission-006", ["goal"], [], ["F3"])


def test_incomplete_live_state_fails_closed(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=lambda: (None, []))
    with pytest.raises(BootstrapFailure, match="incomplete state"):
        b.rehydrate("mission-007", ["goal"], [], ["F3"])
