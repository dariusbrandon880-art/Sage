from sage.c2.build_jump_wave import BIG_JUMP_FLIGHT_IDS, FlightMissionSpec
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher, compute_receipt_hash
from sage.c2.reconvergence_synthesizer import FlightExecutionSummary, LifecycleMilestoneRecord, LifecycleStage, ReconvergenceEvidencePackage


def _missions(prefix="mission"):
    return [
        FlightMissionSpec(
            flight_id=flight_id,
            mission_name=f"{prefix}-{index}",
            target_path=f"target/{prefix}_{index}.py",
            collision_zone=f"target/{prefix}_{index}",
            evidence_ref=f"evidence/{prefix}_{index}.json",
            pr_or_change=f"{prefix.upper()}-{index}",
        )
        for index, flight_id in enumerate(BIG_JUMP_FLIGHT_IDS, start=1)
    ]


def _summary(mission, sha="a" * 40, passed=True):
    return FlightExecutionSummary(
        flight_id=mission.flight_id, target=mission.target_path, classification="ACTIVE",
        execution_result="PASS" if passed else "FAIL", exact_head=sha, tests_passed=3 if passed else 0,
        evidence_ref=mission.evidence_ref, pr_or_change=mission.pr_or_change,
        lifecycle_milestones=[LifecycleMilestoneRecord(stage=stage, passed=passed, evidence_ref=mission.evidence_ref) for stage in LifecycleStage],
    )


def _package(missions, sha="a" * 40, passed=True):
    summaries = [_summary(mission, sha, passed) for mission in missions]
    return ReconvergenceEvidencePackage(
        wave_id="test-wave", flight_summaries=summaries, total_flights=5,
        successful_flights=5 if passed else 0, blocked_flights=0 if passed else 5,
        advancement_matrix_20_cells={f"P{i}-S{s}": passed for i in range(1, 6) for s in range(1, 5)},
        first_pass_verification_rate=100.0 if passed else 0.0,
        reconvergence_verdict="PASS" if passed else "FAIL_CLOSED",
    )


class FakeEngine:
    def __init__(self, package): self.package = package
    def execute_wave(self, wave_id=None, missions=None):
        assert wave_id == "multi-frontier-dispatch"
        assert missions is not None
        return self.package
    def get_current_head_sha(self): return "a" * 40


def test_dispatch_delegates_wave_assigned_missions():
    missions = _missions("first")
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package(missions))).dispatch_all(missions)
    assert receipt.wave_verdict == "PASS"
    assert receipt.summary["source"] == "BuildJumpWaveEngine"
    assert receipt.summary["synthetic_receipts"] is False
    assert len(receipt.flight_receipts) == 5
    assert all(r.status == "PASS" for r in receipt.flight_receipts)
    assert {r.mission_name for r in receipt.flight_receipts} == {m.mission_name for m in missions}


def test_dispatch_accepts_different_missions_on_the_same_five_slots():
    first = _missions("first")
    second = _missions("second")
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package(second))).dispatch_all(second)
    assert receipt.wave_verdict == "PASS"
    assert {r.flight_id for r in receipt.flight_receipts} == set(BIG_JUMP_FLIGHT_IDS)
    assert {r.mission_name for r in receipt.flight_receipts} == {m.mission_name for m in second}
    assert {r.mission_name for r in receipt.flight_receipts} != {m.mission_name for m in first}


def test_dispatch_refuses_stale_execution_sha_per_flight():
    missions = _missions("stale")
    receipt = MultiFrontierDispatcher(commit_sha="a" * 40, engine_factory=lambda: FakeEngine(_package(missions, sha="b" * 40))).dispatch_all(missions)
    assert receipt.wave_verdict == "HOLD"
    assert receipt.collision_count == 5
    assert len(receipt.collisions_detected) == 5
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)
    assert {r.flight_id for r in receipt.flight_receipts} == set(BIG_JUMP_FLIGHT_IDS)


def test_dispatch_refuses_failed_wave():
    missions = _missions("failed")
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package(missions, passed=False))).dispatch_all(missions)
    assert receipt.wave_verdict == "HOLD"
    assert all(r.status == "FAIL" for r in receipt.flight_receipts)


def test_receipt_hash_determinism():
    h1 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    h2 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_1")
    h3 = compute_receipt_hash("Flight A", "mission_1", "scope.a", "proof_type_1", "sha_2")
    assert h1 == h2 and h1 != h3 and len(h1) == 64


def test_serialization_contains_real_execution_metadata():
    missions = _missions("serialize")
    receipt = MultiFrontierDispatcher(engine_factory=lambda: FakeEngine(_package(missions))).dispatch_all(missions)
    data = receipt.to_dict()
    assert data["wave_verdict"] == "PASS"
    assert len(data["flight_receipts"]) == 5
    assert all(item["proof_type"] == "governed_wave_execution_summary" for item in data["flight_receipts"])
    assert data["summary"]["synthetic_receipts"] is False
