from sage.c2.build_jump_wave import FlightMissionSpec
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher, compute_receipt_hash
from sage.c2.reconvergence_synthesizer import FlightExecutionSummary, LifecycleMilestoneRecord, LifecycleStage, ReconvergenceEvidencePackage


def _missions():
    return [
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name=f"Mission {i}",
            target_path=f"target/mission_{i}.py",
            collision_zone=f"target/mission_{i}/",
            evidence_ref=f"evidence/mission_{i}.json",
            pr_or_change=f"mission-{i}",
            test_references=[],
        )
        for i in range(1, 6)
    ]


def _summary(mission, sha="a" * 40, passed=True):
    return FlightExecutionSummary(flight_id=mission.flight_id, target=mission.target_path, classification="ACTIVE", execution_result="PASS" if passed else "FAIL", exact_head=sha, tests_passed=3 if passed else 0, evidence_ref=mission.evidence_ref, pr_or_change=mission.pr_or_change, lifecycle_milestones=[LifecycleMilestoneRecord(stage=stage, passed=passed, evidence_ref=mission.evidence_ref) for stage in LifecycleStage])


def _package(sha="a" * 40, passed=True):
    missions = _missions()
    summaries = [_summary(mission, sha, passed) for mission in missions]
    return ReconvergenceEvidencePackage(wave_id="test-wave", flight_summaries=summaries, total_flights=5, successful_flights=5 if passed else 0, blocked_flights=0 if passed else 5, advancement_matrix_20_cells={f"F{i}-S{s}": passed for i in range(1, 6) for s in range(1, 5)}, first_pass_verification_rate=100.0 if passed else 0.0, reconvergence_verdict="PASS" if passed else "FAIL_CLOSED")


class FakeEngine:
    def __init__(self, package): self.package = package
    def execute_wave(self, wave_id=None, missions=None):
        assert wave_id == "multi-frontier-dispatch"
        assert [m.flight_id for m in missions] == ["F1", "F2", "F3", "F4", "F5"]
        return self.package
    def get_current_head_sha(self): return "a" * 40


def test_dispatch_delegates_to_canonical_wave_engine():
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package())).dispatch_all(_missions())
    assert receipt.wave_verdict == "PASS"
    assert receipt.summary["source"] == "BuildJumpWaveEngine"
    assert receipt.summary["synthetic_receipts"] is False
    assert receipt.summary["flight_assignment_model"] == "open_reusable_slots"
    assert len(receipt.flight_receipts) == 5
    assert all(r.status == "PASS" for r in receipt.flight_receipts)


def test_dispatch_refuses_stale_execution_sha_per_flight():
    receipt = MultiFrontierDispatcher(commit_sha="a" * 40, engine_factory=lambda: FakeEngine(_package(sha="b" * 40))).dispatch_all(_missions())
    assert receipt.wave_verdict == "HOLD"
    assert receipt.collision_count == 5
    assert len(receipt.collisions_detected) == 5
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)


def test_dispatch_refuses_failed_wave():
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package(passed=False))).dispatch_all(_missions())
    assert receipt.wave_verdict == "HOLD"
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)


def test_dispatch_rejects_non_five_assignments():
    missions = _missions()[:4]
    try:
        MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package())).dispatch_all(missions)
    except ValueError as exc:
        assert "exactly 5" in str(exc)
    else:
        raise AssertionError("expected five-slot validation failure")


def test_receipt_hash_determinism():
    h1 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    h2 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    h3 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_2")
    assert h1 == h2 and h1 != h3 and len(h1) == 64


def test_serialization_contains_real_execution_metadata():
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package())).dispatch_all(_missions())
    data = receipt.to_dict()
    assert data["wave_verdict"] == "PASS"
    assert len(data["flight_receipts"]) == 5
    assert all(item["proof_type"] == "governed_wave_execution_summary" for item in data["flight_receipts"])
    assert data["summary"]["synthetic_receipts"] is False
