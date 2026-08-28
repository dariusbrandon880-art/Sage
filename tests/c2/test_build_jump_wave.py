"""Unit and integration tests for SAGE Big Jump Wave Engine & Evidence Verification."""

import json
import re
import threading
from pathlib import Path
import pytest

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec
from sage.c2.reconvergence_synthesizer import FlightExecutionSummary, LifecycleMilestoneRecord, LifecycleStage


@pytest.fixture
def build_jump_engine(tmp_path):
    return BuildJumpWaveEngine(storage_dir=str(tmp_path))


def test_build_jump_wave_head_sha(build_jump_engine):
    sha = build_jump_engine.get_current_head_sha()
    assert len(sha) == 40
    assert re.match(r"^[0-9a-fA-F]{40}$", sha)


def test_build_jump_wave_execution_full(build_jump_engine):
    pkg = build_jump_engine.execute_wave(wave_id="test-wave-unit")

    assert pkg.wave_id == "test-wave-unit"
    assert pkg.total_flights == 5
    assert pkg.successful_flights == 5
    assert pkg.blocked_flights == 0
    assert pkg.reconvergence_verdict == "PASS"
    assert pkg.first_pass_verification_rate == 100.0

    matrix = pkg.advancement_matrix_20_cells
    assert len(matrix) == 20
    assert all(matrix.values())

    for summary in pkg.flight_summaries:
        assert summary.execution_result == "PASS"
        assert len(summary.exact_head) == 40
        assert summary.completed_all_stages() is True
        assert summary.blocker is None


def test_build_jump_wave_runs_independent_flights_concurrently(build_jump_engine, monkeypatch):
    thread_ids = set()
    start_barrier = threading.Barrier(5)

    def fake_run_flight(spec, wave_id, head_sha):
        thread_ids.add(threading.get_ident())
        start_barrier.wait(timeout=5)
        lifecycle_milestones = [
            LifecycleMilestoneRecord(
                stage=stage,
                passed=True,
                evidence_ref=spec.evidence_ref,
            )
            for stage in LifecycleStage
        ]
        return FlightExecutionSummary(
            flight_id=spec.flight_id,
            target=spec.target_path,
            classification="ACTIVE",
            execution_result="PASS",
            exact_head=head_sha,
            tests_passed=1,
            evidence_ref=spec.evidence_ref,
            pr_or_change=spec.pr_or_change,
            lifecycle_milestones=lifecycle_milestones,
        )

    monkeypatch.setattr(build_jump_engine, "_run_flight", fake_run_flight)
    package = build_jump_engine.execute_wave(wave_id="parallel-wave-test")

    assert package.reconvergence_verdict == "PASS"
    assert package.total_flights == 5
    assert package.successful_flights == 5
    assert len(thread_ids) == 5


def test_build_jump_wave_invalid_mission_count(build_jump_engine):
    invalid_missions = [
        FlightMissionSpec(
            flight_id="F1",
            frontier_name="F1",
            target_path="t1.py",
            collision_zone="ns1",
            evidence_ref="e1.json",
            pr_or_change="PR1",
        )
    ]
    with pytest.raises(ValueError, match="Big Jump Wave requires exactly 5 flight missions"):
        build_jump_engine.execute_wave(missions=invalid_missions)


def test_persisted_build_jump_wave_evidence():
    evidence_path = Path("evidence_capture/build_jump_wave_evidence.json")
    assert evidence_path.exists(), "build_jump_wave_evidence.json must exist"

    with open(evidence_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_flights"] == 5
    assert data["successful_flights"] == 5
    assert data["reconvergence_verdict"] == "PASS"
    assert len(data["advancement_matrix_20_cells"]) == 20
    assert all(data["advancement_matrix_20_cells"].values())
    assert len(data["package_hash"]) == 64

    sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
    for summary in data["flight_summaries"]:
        assert summary["execution_result"] == "PASS"
        assert sha_pattern.match(summary["exact_head"])
