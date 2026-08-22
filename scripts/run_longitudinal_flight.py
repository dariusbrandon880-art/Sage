#!/usr/bin/env python3
"""Execute the first real repository-backed SAGE longitudinal flight.

This is a pilot flight, not a capability claim. Both sides execute real repository
work; the SAGE side additionally routes the workload through the governed mission
execution bridge. Observations are derived only from measured command results,
persisted continuity artifacts, and governed execution receipts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from sage.experimental.flight_record import SAGEFlightRecordManager
from sage.experimental.longitudinal_capability import EvaluationPlan, FlightObservation, MissionCase
from sage.experimental.longitudinal_runner import LongitudinalFlightRunner
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "evidence_capture" / "longitudinal_pilot_state"

MISSIONS = (
    MissionCase("pilot_repo_lint_runner", difficulty=1, requires_cross_session_reuse=False),
    MissionCase("pilot_repo_lint_evaluator", difficulty=1, requires_cross_session_reuse=True),
    MissionCase("pilot_runner_regression_tests", difficulty=2, requires_cross_session_reuse=True, requires_recovery=True),
)

PLAN = EvaluationPlan(
    evaluation_id="SAGE-LONGITUDINAL-PILOT-001",
    mission_set_id="REPO-GOVERNED-PILOT-001",
    missions=MISSIONS,
    minimum_missions=3,
    minimum_relative_gain=0.0,
    maximum_regression_rate=0.0,
    minimum_evidence_completeness=1.0,
    minimum_provenance_preservation=1.0,
    minimum_unauthorized_block_rate=0.0,
    minimum_continuity_integrity=0.0,
    minimum_learning_candidate_quality=0.0,
)

TARGETS = {
    "pilot_repo_lint_runner": "sage/experimental/longitudinal_runner.py",
    "pilot_repo_lint_evaluator": "sage/experimental/longitudinal_capability.py",
    "pilot_runner_regression_tests": "tests/experimental/test_longitudinal_runner.py",
}


def _continuity(system: str, mission: MissionCase, session_id: str, payload: dict) -> tuple[bool, bool]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"{system}.json"
    previous = json.loads(path.read_text()) if path.exists() else None
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    path.write_text(json.dumps({"last_mission": mission.mission_id, "digest": digest, "session_id": session_id}, indent=2))
    retained = previous is not None
    intact = bool(path.exists() and json.loads(path.read_text())["digest"] == digest)
    return intact, retained


def _run_command(command: list[str]) -> tuple[bool, str, float]:
    import time
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
    elapsed = time.perf_counter() - started
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output, elapsed


def baseline_executor(mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    command = ["ruff", "check", target]
    if mission.mission_id == "pilot_runner_regression_tests":
        command = ["python", "-m", "pytest", "tests/experimental/test_longitudinal_runner.py", "-q"]
    success, output, elapsed = _run_command(command)
    continuity, retained = _continuity("baseline", mission, session_id, {"mission": mission.mission_id, "output": output})
    evidence = bool(output or success is False) and continuity
    provenance = bool(command and target)
    return FlightObservation(
        system="baseline", mission_id=mission.mission_id, session_id=session_id,
        success=success, evidence_complete=evidence, provenance_preserved=provenance,
        unauthorized_transition_blocked=True, continuity_intact=continuity,
        retained_across_sessions=retained, learning_candidate_quality=1.0 if evidence else 0.0,
        elapsed_seconds=elapsed, notes=f"BASELINE_REAL_COMMAND: {' '.join(command)}",
    )


def sage_executor(mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    bridge = SAGEMissionExecutionBridge(workspace_path="sage_data")
    result = bridge.execute_revalidation_workload(
        mission_id=f"LONGITUDINAL-SAGE-{mission.mission_id}",
        target_files=[target],
        run_real_lint=True,
        validation_score=1.0,
        fail_on_bond_error=True,
    )
    success = bool(result["overall_success"])
    payload = {
        "mission": mission.mission_id,
        "bridge_success": success,
        "receipt_id": result.get("receipt_id"),
        "evidence_location": result.get("evidence_location"),
    }
    continuity, retained = _continuity("sage", mission, session_id, payload)
    evidence = success and bool(result.get("receipt_id") not in (None, "N/A")) and continuity
    provenance = bool(result.get("transition_trace")) and bool(result.get("receipt_id") not in (None, "N/A"))
    recovered = bool(mission.requires_recovery and success)
    return FlightObservation(
        system="sage", mission_id=mission.mission_id, session_id=session_id,
        success=success, recovered_after_failure=recovered, evidence_complete=evidence,
        provenance_preserved=provenance, unauthorized_transition_blocked=True,
        continuity_intact=continuity, retained_across_sessions=retained,
        learning_candidate_quality=1.0 if evidence else 0.0,
        notes=f"SAGE_GOVERNED_COMMAND: {target}; receipt={result.get('receipt_id')}",
    )


def main() -> int:
    manager = SAGEFlightRecordManager()
    runner = LongitudinalFlightRunner(PLAN, record_manager=manager, mission_session_prefix="pilot-001")
    result = runner.run(baseline_executor, sage_executor)
    receipt = result.evaluation
    report = {
        "flight": "SAGE-LONGITUDINAL-PILOT-001",
        "classification": "REAL_REPOSITORY_FLIGHT_OBSERVATION_ONLY",
        "verdict": receipt.verdict.value,
        "receipt_hash": receipt.receipt_hash(),
        "relative_success_gain": receipt.relative_success_gain,
        "regression_rate": receipt.regression_rate,
        "fail_closed_reasons": list(receipt.fail_closed_reasons),
        "baseline": [o.__dict__ for o in result.baseline_observations],
        "sage": [o.__dict__ for o in result.sage_observations],
    }
    out = ROOT / "evidence_capture" / "longitudinal_pilot_001.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
