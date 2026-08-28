from __future__ import annotations

from sage.c2.build_jump_wave import CANONICAL_BIG_JUMP_MISSIONS
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher, compute_receipt_hash
from sage.c2.reconvergence_synthesizer import (
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
    ReconvergenceEvidencePackage,
)


def _summary(mission, sha="a" * 40, passed=True):
    return FlightExecutionSummary(
        flight_id=mission.flight_id,
        target=mission.target_path,
        classification="ACTIVE",
        execution_result="PASS" if passed else "FAIL",
        exact_head=sha,
        tests_passed=3 if passed else 0,
        evidence_ref=mission.evidence_ref,
        pr_or_change=mission.pr_or_change,
        lifecycle_milestones=[
            LifecycleMilestoneRecord(stage=stage, passed=passed, evidence_ref=mission.evidence_ref)
            for stage in LifecycleStage
        ],
    )


def _package(sha="a" * 40, passed=True):
    summaries = [_summary(mission, sha, passed) for mission in CANONICAL_BIG_JUMP_MISSIONS]
    return ReconvergenceEvidencePackage(
        wave_id="test-wave",
        flight_summaries=summaries,
        total_flights=5,
        successful_flights=5 if passed else 0,
        blocked_flights=0 if passed else 5,
        advancement_matrix_20_cells={f"P{i}-S{s}": passed for i in range(1, 6) for s in range(1, 5)},
        first_pass_verification_rate=100.0 if passed else 0.0,
        reconvergence_verdict="PASS" if passed else "FAIL_CLOSED",
    )


class FakeEngine:
    def __init__(self, package):
        self.package = package

    def execute_wave(self, wave_id=None):
        assert wave_id == "multi-frontier-dispatch"
        return self.package

    def get_current_head_sha(self):
        return "a" * 40


def test_dispatch_delegates_to_canonical_wave_engine():
    package = _package()
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(package)).dispatch_all()
    assert receipt.wave_verdict == "PASS"
    assert receipt.summary["source"] == "BuildJumpWaveEngine"
    assert receipt.summary["synthetic_receipts"] is False
    assert len(receipt.flight_receipts) == 5
    assert all(r.status == "PASS" for r in receipt.flight_receipts)


def test_dispatch_refuses_stale_execution_sha():
    package = _package(sha="b" * 40)
    receipt = MultiFrontierDispatcher(
        commit_sha="a" * 40,
        engine_factory=lambda: FakeEngine(package),
    ).dispatch_all()
    assert receipt.wave_verdict == "HOLD"
    assert receipt.collision_count == 5
    assert "stale or mismatched flight commit SHA detected" in receipt.collisions_detected
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)


def test_dispatch_refuses_failed_wave():
    package = _package(passed=False)
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(package)).dispatch_all()
    assert receipt.wave_verdict == "HOLD"
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)


def test_receipt_hash_determinism():
    hash1 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash2 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    hash3 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_2")
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_serialization_contains_real_execution_metadata():
    package = _package()
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(package)).dispatch_all()
    as_dict = receipt.to_dict()
    assert as_dict["wave_verdict"] == "PASS"
    assert len(as_dict["flight_receipts"]) == 5
    assert all(item["proof_type"] == "governed_wave_execution_summary" for item in as_dict["flight_receipts"])
    assert as_dict["summary"]["synthetic_receipts"] is False
