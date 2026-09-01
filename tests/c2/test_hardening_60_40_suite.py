"""Adversarial Hardening Test Suite for SAGE 60/40 Operating Architecture.

Tests fail-closed boundaries, lock collision resistance, anti-drift state reconciliation,
TransitionAuthorityEngine state-digest validation, and exact-HEAD contract validation.
"""

import pytest

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec, validate_wave_missions
from sage.c2.double_big_jump_contract import (
    DoubleBigJumpWaveSpec,
    reconverge_double_big_jump,
    require_current_head,
)
from sage.c2.execution_intelligence import (
    AdaptiveConcurrencyGovernor,
    ConcurrencyValidationStatus,
    ExecutionAdmissionStatus,
    ExecutionAdmissionThrottler,
    WorkflowVelocityController,
)
from sage.c2.governance_intelligence import (
    GovernanceProofAttackAuditor,
    GovernanceProvenanceValidator,
)
from sage.core.attestation_receipt import AttestationDecision, AttestationReceipt
from sage.core.transition_engine import (
    ReplayAttestationError,
    StaleAuthorizationError,
    TransitionAuthorityEngine,
    TransitionRequest,
    compute_capability_state_digest,
)


def test_build_jump_wave_engine_fails_closed_without_explicit_missions() -> None:
    engine = BuildJumpWaveEngine()
    with pytest.raises(ValueError, match="Big Jump Wave requires an explicit mission plan"):
        engine.execute_wave("wave-test", missions=None)


def test_validate_wave_missions_requires_exact_five_slots() -> None:
    bad_missions = [
        FlightMissionSpec(
            flight_id="F1",
            frontier_name="front-1",
            target_path="sage/c2/target.py",
            collision_zone="sage.c2.target",
            evidence_ref="evidence/f1.json",
            pr_or_change="PR #1",
        )
    ]
    with pytest.raises(ValueError, match="requires exactly 5 flight missions"):
        validate_wave_missions(bad_missions)


def test_double_big_jump_contract_rejects_duplicate_mission_names() -> None:
    missions = tuple(
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name="duplicate-frontier",
            target_path=f"sage/c2/target_{i}.py",
            collision_zone=f"sage.c2.target_{i}",
            evidence_ref=f"evidence/f{i}.json",
            pr_or_change=f"PR #{i}",
        )
        for i in range(1, 6)
    )
    spec = DoubleBigJumpWaveSpec(wave_id="wave-1", missions=missions)
    with pytest.raises(ValueError, match="mission identities must be unique"):
        spec.validate()


def test_require_current_head_fails_closed_on_sha_mismatch() -> None:
    with pytest.raises(ValueError, match="repository HEAD mismatch"):
        require_current_head("27be9e8094a16209290b7c5ae04c2fdec1ccd7c2", "bf2560ede2899adfe73fe2e2cfb4accd0b8885e2")


def test_require_current_head_fails_closed_on_none() -> None:
    with pytest.raises(ValueError, match="requires independently verified"):
        require_current_head(None, "27be9e8094a16209290b7c5ae04c2fdec1ccd7c2")


def test_adaptive_concurrency_governor_hold_status_and_risk_throttling() -> None:
    governor = AdaptiveConcurrencyGovernor(min_workers=1, max_workers=16)
    profile = governor.calculate_safe_concurrency(
        wave_id="wave-high-risk",
        requested_workers=16,
        lock_contention_rate=0.8,
        verification_latency_ms=2500.0,
        rework_rate=0.5,
        cpu_load_factor=0.9,
    )
    assert profile.recommended_workers <= 4
    assert profile.validation_status == ConcurrencyValidationStatus.HOLD
    assert profile.risk_score > 0.7


def test_execution_admission_throttler_rejects_high_risk_flights() -> None:
    throttler = ExecutionAdmissionThrottler(max_capacity=10)
    res = throttler.request_admission(flight_id="F1", risk_score=0.95)
    assert res["status"] == ExecutionAdmissionStatus.REJECTED_HIGH_RISK
    assert res["admitted"] is False


def test_workflow_velocity_controller_rejects_invalid_sha() -> None:
    controller = WorkflowVelocityController()
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        controller.execute_execution_intelligence_wave(
            wave_id="wave-invalid",
            exact_git_head="invalid_head_sha",
            flights=[{"flight_id": "F1"}],
        )


def test_governance_proof_attack_auditor_neutralizes_stale_sha_claims() -> None:
    auditor = GovernanceProofAttackAuditor()
    res = auditor.audit_stale_evidence_attack(
        legacy_sha="39411847",
        current_head="27be9e8094a16209290b7c5ae04c2fdec1ccd7c2",
    )
    assert res.neutralized is True
    assert "Stale or mismatched evidence SHA rejected" in res.rejection_reason


def test_governance_provenance_validator_rejects_invalid_station() -> None:
    validator = GovernanceProvenanceValidator()
    res = validator.audit_station_spoof_attack("[C2::UNKNOWN_AGENT]")
    assert res.neutralized is True
    assert "non-canonical station identity tag rejected" in res.rejection_reason


def test_transition_engine_fails_closed_on_stale_state_digest() -> None:
    initial_state = {"agent_1:cap_a": "QUALIFIED"}
    initial_digest = compute_capability_state_digest(initial_state)

    engine = TransitionAuthorityEngine(
        trusted_reviewer_keys={"reviewer_1": "key_1"},
        signature_verifier=lambda receipt, key: True,
        capability_state=initial_state,
    )

    receipt = AttestationReceipt(
        assessment_digest="digest_assess_1",
        sufficiency_digest="digest_suff_1",
        capability_id="cap_a",
        subject_id="agent_1",
        policy_version="p1",
        reviewer_id="reviewer_1",
        authorization_scope="scope_a",
        attested_at="2026-08-31T20:00:00Z",
        decision=AttestationDecision.APPROVED,
        signature="sig_001",
    )

    # Mutate state before executing request
    initial_state["agent_1:cap_b"] = "QUALIFIED"

    request = TransitionRequest(
        capability_id="cap_a",
        subject_id="agent_1",
        policy_version="p1",
        authorization_scope="scope_a",
        target_state="PROMOTED",
        authorization_state_digest=initial_digest,
    )

    with pytest.raises(StaleAuthorizationError, match="authorization state digest is stale"):
        engine.execute(receipt, request)


def test_transition_engine_fails_closed_on_replayed_receipt() -> None:
    initial_state = {"agent_1:cap_a": "QUALIFIED"}
    digest = compute_capability_state_digest(initial_state)

    receipt = AttestationReceipt(
        assessment_digest="digest_assess_1",
        sufficiency_digest="digest_suff_1",
        capability_id="cap_a",
        subject_id="agent_1",
        policy_version="p1",
        reviewer_id="reviewer_1",
        authorization_scope="scope_a",
        attested_at="2026-08-31T20:00:00Z",
        decision=AttestationDecision.APPROVED,
        signature="sig_001",
    )

    engine = TransitionAuthorityEngine(
        trusted_reviewer_keys={"reviewer_1": "key_1"},
        signature_verifier=lambda receipt, key: True,
        capability_state=initial_state,
        consumed_receipt_ids={receipt.receipt_id},
    )

    request = TransitionRequest(
        capability_id="cap_a",
        subject_id="agent_1",
        policy_version="p1",
        authorization_scope="scope_a",
        target_state="PROMOTED",
        authorization_state_digest=digest,
    )

    with pytest.raises(ReplayAttestationError, match="has already been consumed"):
        engine.execute(receipt, request)


def test_reconverge_double_big_jump_fails_closed_if_one_wave_fails() -> None:
    missions_a = tuple(
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name=f"A-{i}",
            target_path=f"sage/c2/a_{i}.py",
            collision_zone=f"sage.c2.a_{i}",
            evidence_ref=f"evidence/a_{i}.json",
            pr_or_change=f"PR A{i}",
        )
        for i in range(1, 6)
    )
    missions_b = tuple(
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name=f"B-{i}",
            target_path=f"sage/c2/b_{i}.py",
            collision_zone=f"sage.c2.b_{i}",
            evidence_ref=f"evidence/b_{i}.json",
            pr_or_change=f"PR B{i}",
        )
        for i in range(1, 6)
    )
    wave_a = DoubleBigJumpWaveSpec(wave_id="wave-A", missions=missions_a)
    wave_b = DoubleBigJumpWaveSpec(wave_id="wave-B", missions=missions_b)

    results = {"wave-A": True, "wave-B": False}
    verdict = reconverge_double_big_jump(wave_results=results, waves=(wave_a, wave_b))
    assert verdict is False
