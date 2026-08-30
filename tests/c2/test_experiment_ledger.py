"""Unit tests for SAGE C2 ExperimentLedger engine and Big Jump Wave integration."""

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from sage.c2.experiment_ledger import (
    CandidateComparison,
    CounterexampleRecord,
    ExperimentBaseline,
    ExperimentLedger,
    ValidationStatus,
)
from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec


def test_experiment_ledger_registration_and_retrieval(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))

    baseline = ExperimentBaseline(
        metric_name="latency_ms",
        baseline_value=120.0,
        target_value=50.0,
        units="ms",
        notes="Target under 50ms",
    )
    rec = ledger.register_experiment(
        experiment_id="exp_001",
        hypothesis="Parallel dispatch reduces latency.",
        wave_id="wave_test_01",
        flight_id="FLIGHT-F1",
        commit_sha="abcd1234efgh5678abcd1234efgh5678abcd1234",
        baselines=[baseline],
    )

    assert rec.experiment_id == "exp_001"
    assert rec.status == ValidationStatus.HOLD
    assert len(rec.baselines) == 1
    assert rec.baselines[0].metric_name == "latency_ms"

    retrieved = ledger.get_experiment("exp_001")
    assert retrieved is not None
    assert retrieved.hypothesis == "Parallel dispatch reduces latency."


def test_experiment_ledger_evidence_and_counterexample(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))

    ledger.register_experiment(
        experiment_id="exp_002",
        hypothesis="Test evidence addition",
        wave_id="wave_02",
        flight_id="FLIGHT-F2",
        commit_sha="1234567890123456789012345678901234567890",
    )

    ev_file = tmp_path / "ev_proof.json"
    ev_file.write_text(json.dumps({"proof": True}) + "\n", encoding="utf-8")

    ledger.add_evidence_ref("exp_002", str(ev_file))
    ledger.add_observation("exp_002", "Initial run succeeded.")

    cx = CounterexampleRecord(
        counterexample_id="cx_001",
        description="High load caused brief delay.",
        impact_severity="MEDIUM",
        evidence_ref=str(ev_file),
    )
    ledger.add_counterexample("exp_002", cx)

    rec = ledger.get_experiment("exp_002")
    assert rec is not None
    assert str(ev_file) in rec.evidence_refs
    assert "Initial run succeeded." in rec.observations
    assert len(rec.counterexamples) == 1
    assert rec.counterexamples[0].counterexample_id == "cx_001"


def test_experiment_ledger_candidate_comparison(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))

    ledger.register_experiment(
        experiment_id="exp_003",
        hypothesis="Candidate B outperforms Candidate A",
        wave_id="wave_03",
        flight_id="FLIGHT-F3",
        commit_sha="0000000000000000000000000000000000000000",
    )

    comp = CandidateComparison(
        candidate_id="cand_b",
        technique_name="Async Dispatch",
        metric_name="throughput_qps",
        baseline_metric=100.0,
        candidate_metric=250.0,
        delta=150.0,
        verdict="WIN",
    )
    ledger.add_candidate_comparison("exp_003", comp)

    rec = ledger.get_experiment("exp_003")
    assert rec is not None
    assert len(rec.candidate_comparisons) == 1
    assert rec.candidate_comparisons[0].verdict == "WIN"


def test_experiment_ledger_validation_decision_fail_closed(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))

    ledger.register_experiment(
        experiment_id="exp_004",
        hypothesis="Fail closed without valid evidence file",
        wave_id="wave_04",
        flight_id="FLIGHT-F4",
        commit_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )

    # Attempt promotion with zero evidence refs -> defaults to HOLD
    rec = ledger.update_validation_decision("exp_004", ValidationStatus.PROMOTED, notes="Attempting promotion")
    assert rec.status == ValidationStatus.HOLD
    assert "PROMOTION REJECTED: Zero evidence refs attached" in rec.validation_notes

    # Add non-existent file ref
    missing_file = tmp_path / "missing.json"
    ledger.add_evidence_ref("exp_004", str(missing_file))
    rec = ledger.update_validation_decision("exp_004", ValidationStatus.PROMOTED, notes="Attempt 2")
    assert rec.status == ValidationStatus.HOLD
    assert "missing on disk" in rec.validation_notes

    # Create real evidence file -> Promotion succeeds
    missing_file.write_text(json.dumps({"status": "PASS"}) + "\n", encoding="utf-8")
    rec = ledger.update_validation_decision("exp_004", ValidationStatus.PROMOTED, notes="Valid file attached")
    assert rec.status == ValidationStatus.PROMOTED


def test_experiment_ledger_restart_recovery(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_ledger.json"
    ledger1 = ExperimentLedger(ledger_path=str(ledger_file))

    ledger1.register_experiment(
        experiment_id="exp_persisted",
        hypothesis="Persistence across instances",
        wave_id="wave_persisted",
        flight_id="FLIGHT-PERSIST",
        commit_sha="1111111111111111111111111111111111111111",
    )
    ledger1.add_observation("exp_persisted", "Recorded before shutdown.")

    # Re-instantiate ledger pointing to same JSON file
    ledger2 = ExperimentLedger(ledger_path=str(ledger_file))
    rec = ledger2.get_experiment("exp_persisted")
    assert rec is not None
    assert rec.hypothesis == "Persistence across instances"
    assert "Recorded before shutdown." in rec.observations


def test_experiment_ledger_concurrent_writes(tmp_path: Path) -> None:
    ledger_file = tmp_path / "test_concurrent_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))

    ledger.register_experiment(
        experiment_id="exp_concurrent",
        hypothesis="Thread safety check",
        wave_id="wave_conc",
        flight_id="FLIGHT-CONC",
        commit_sha="9999999999999999999999999999999999999999",
    )

    def worker(i: int):
        ledger.add_observation("exp_concurrent", f"Observation from thread {i}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        for f in futures:
            f.result()

    rec = ledger.get_experiment("exp_concurrent")
    assert rec is not None
    assert len(rec.observations) == 20


def test_build_jump_wave_experiment_ledger_integration(tmp_path: Path) -> None:
    ledger_file = tmp_path / "wave_exp_ledger.json"
    ledger = ExperimentLedger(ledger_path=str(ledger_file))
    engine = BuildJumpWaveEngine(storage_dir=str(tmp_path / "evidence"), experiment_ledger=ledger)

    mission = FlightMissionSpec(
        flight_id="FLIGHT-TEST-EXP",
        frontier_name="Test Experiment Frontier",
        target_path="sage/c2/experiment_ledger.py",
        collision_zone="sage/c2/exp_test/",
        evidence_ref=str(tmp_path / "test_exp_evidence.json"),
        pr_or_change="Test Experiment Flight",
        test_references=["tests/c2/test_experiment_ledger.py"],
    )

    res = engine.execute_wave(wave_id="wave_exp_test", missions=[mission, mission, mission, mission, mission])
    assert res.overall_verdict == "PASS"

    experiments = ledger.list_experiments()
    assert len(experiments) > 0
    exp_record = ledger.get_experiment("exp_wave_exp_test_FLIGHT-TEST-EXP")
    assert exp_record is not None
    assert exp_record.status == ValidationStatus.PROMOTED
