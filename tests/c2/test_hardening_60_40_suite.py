"""Adversarial Hardening Test Suite for SAGE 60/40 Operating Architecture.

Tests fail-closed boundaries, lock collision resistance, anti-drift state reconciliation,
and exact-HEAD contract validation across C2 substrates.
"""

import pytest

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec, validate_wave_missions
from sage.c2.double_big_jump_contract import (
    DoubleBigJumpWaveSpec,
    reconverge_double_big_jump,
    require_current_head,
    validate_double_big_jump_waves,
)
from sage.c2.execution_intelligence import (
    AdaptiveConcurrencyGovernor,
    ConcurrencyValidationStatus,
    ExecutionAdmissionStatus,
    ExecutionAdmissionThrottler,
    WorkflowVelocityController,
)
from sage.c2.governance_intelligence import (
    AntiDriftVerificationEngine,
    GovernanceProofAttackAuditor,
    GovernanceProvenanceValidator,
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
        require_current_head("172c3227a791dfb6b3da9db4e64ea779c19d16f5", "bf2560ede2899adfe73fe2e2cfb4accd0b8885e2")


def test_require_current_head_fails_closed_on_none() -> None:
    with pytest.raises(ValueError, match="requires independently verified"):
        require_current_head(None, "172c3227a791dfb6b3da9db4e64ea779c19d16f5")


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
        current_head="172c3227a791dfb6b3da9db4e64ea779c19d16f5",
    )
    assert res.neutralized is True
    assert "Stale or mismatched evidence SHA rejected" in res.rejection_reason


def test_governance_provenance_validator_rejects_invalid_station() -> None:
    validator = GovernanceProvenanceValidator()
    res = validator.audit_station_spoof_attack("[C2::UNKNOWN_AGENT]")
    assert res.neutralized is True
    assert "non-canonical station identity tag rejected" in res.rejection_reason


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
