import json
import pytest
from sage.c2.mission_continuity import CANONICAL_MAIN_GOALS
from sage.c2.operator_acceptance_bootstrap import BootstrapFailure, OperatorAcceptanceBootstrap

VALID_SHA = "a" * 40
REQUIRED = ["chatgpt", "gemini", "jules"]
CANONICAL_GOALS = list(CANONICAL_MAIN_GOALS)


def fake_git(*args):
    assert args == ("rev-parse", "HEAD")
    return VALID_SHA


def bootstrap(tmp_path, provider=lambda: ([], [])):
    return OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=fake_git, state_provider=provider)


def state_for(tmp_path, provider=lambda: ([], [])):
    return bootstrap(tmp_path, provider).rehydrate(
        "mission-001", CANONICAL_GOALS, ["side goal"], ["F1", "F2", "F3"], REQUIRED
    )


def test_cold_start_rehydrates_and_locks_execution(tmp_path):
    b = bootstrap(tmp_path, lambda: (["PR #286"], ["Issue #901"]))
    state = b.rehydrate("mission-001", CANONICAL_GOALS, ["side goal"], ["F1", "F2"], REQUIRED)
    b.require_execution_ready(state)
    assert state.canonical_git_sha == VALID_SHA
    assert state.active_prs == ["PR #286"] and state.active_issues == ["Issue #901"]
    assert state.interface_verdicts == {interface: "PENDING" for interface in REQUIRED}
    assert state.deterministic_gate.checks["canonical_mission_hierarchy"] is True
    assert state.empirical_gate.status == "PENDING"


def test_partial_surface_pass_stays_pending(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    b.capture_operator_observation(state, "gemini", "PASS", "evidence://gemini-pass")
    assert state.interface_verdicts["gemini"] == "PASS"
    assert state.empirical_gate.status == "PENDING"
    assert state.acceptance_status == "ENGINEERING_VERIFIED"


def test_full_multi_surface_pass_converges_to_accepted(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    for interface in REQUIRED:
        b.capture_operator_observation(state, interface, "PASS", f"evidence://{interface}-pass")
    assert state.empirical_gate.status == "PASS"
    assert state.empirical_gate.checks["full_surface_convergence"] is True
    assert state.acceptance_status == "ACCEPTED"


def test_any_required_surface_failure_blocks_acceptance_and_elevates_defect(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    b.capture_operator_observation(state, "chatgpt", "PASS", "evidence://chatgpt-pass")
    b.capture_operator_observation(state, "gemini", "FAIL", "evidence://gemini-fail", "C2-OPS-003")
    assert state.empirical_gate.status == "FAIL"
    assert state.acceptance_status == "NOT_ACCEPTED"
    assert "C2-OPS-003" in state.open_defects


def test_unknown_interface_is_rejected(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    with pytest.raises(BootstrapFailure, match="not required"):
        b.capture_operator_observation(state, "other", "PASS", "evidence://other")


def test_required_interfaces_are_mandatory_and_unique(tmp_path):
    b = bootstrap(tmp_path)
    with pytest.raises(BootstrapFailure, match="at least one required"):
        b.rehydrate("mission", CANONICAL_GOALS, [], [], [])
    with pytest.raises(BootstrapFailure, match="must be unique"):
        b.rehydrate("mission", CANONICAL_GOALS, [], [], ["chatgpt", "chatgpt"])


def test_noncanonical_main_goal_is_rejected(tmp_path):
    b = bootstrap(tmp_path)
    with pytest.raises(BootstrapFailure, match="first main goal must preserve canonical priority"):
        b.rehydrate("mission-003", ["complete main mission"], [], [], REQUIRED)


def test_cold_start_drift_fails_closed_on_invalid_head(tmp_path):
    b = OperatorAcceptanceBootstrap(repo_root=tmp_path, git_runner=lambda *args: "bad-head", state_provider=lambda: ([], []))
    with pytest.raises(BootstrapFailure, match="40-character SHA"):
        b.rehydrate("mission-004", CANONICAL_GOALS, [], [], REQUIRED)


def test_missing_operator_evidence_fails_closed(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    with pytest.raises(BootstrapFailure, match="evidence_ref is required"):
        b.capture_operator_observation(state, "chatgpt", "PASS", "")


def test_live_state_provider_failure_fails_closed(tmp_path):
    b = bootstrap(tmp_path, lambda: (_ for _ in ()).throw(RuntimeError("connector down")))
    with pytest.raises(BootstrapFailure, match="unable to reconcile live state"):
        b.rehydrate("mission-006", CANONICAL_GOALS, [], ["F3"], REQUIRED)


def test_incomplete_live_state_fails_closed(tmp_path):
    b = bootstrap(tmp_path, lambda: (None, []))
    with pytest.raises(BootstrapFailure, match="incomplete state"):
        b.rehydrate("mission-007", CANONICAL_GOALS, [], ["F3"], REQUIRED)


def test_evidence_receipt_preserves_multi_surface_state(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    b.capture_operator_observation(state, "chatgpt", "PASS", "evidence://chatgpt-pass")
    receipt = b.evidence_receipt(state, tmp_path / "receipt.json")
    data = json.loads(receipt.read_text())
    assert data["interface_verdicts"]["chatgpt"] == "PASS"
    assert data["interface_verdicts"]["gemini"] == "PENDING"
    assert data["receipt_hash"]


def test_customer_surface_identity_binding_and_reconciliation(tmp_path):
    b = bootstrap(tmp_path)
    state = state_for(tmp_path)
    assert state.customer_surface.bound is True
    assert state.customer_surface.customer_id == "SAGE_INTERNAL_BUILDER"

    b.bind_customer_surface(state, "EXTERNAL_CUSTOMER_001", "CUSTOM_CLIENT_SURFACE", "DIRECTOR_AGENT")
    assert state.customer_surface.customer_id == "EXTERNAL_CUSTOMER_001"
    assert state.customer_surface.customer_surface == "CUSTOM_CLIENT_SURFACE"
    assert state.customer_surface.agent_identity == "DIRECTOR_AGENT"
    assert state.customer_surface.bound is True

    with pytest.raises(BootstrapFailure, match="customer_id and customer_surface are required"):
        b.bind_customer_surface(state, "", "CUSTOM_CLIENT_SURFACE")
