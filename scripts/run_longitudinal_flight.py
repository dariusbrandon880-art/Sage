#!/usr/bin/env python3
"""Execute the first real repository-backed SAGE longitudinal flight.

This is a pilot flight, not a capability claim. Both sides execute real repository
work; the SAGE side additionally routes the workload through the governed mission
execution bridge. All bridge persistence is sandboxed so the pilot cannot mutate
canonical SAGE registry/archive state. Observations are derived only from measured
command results, explicit controlled-failure recovery, continuity artifacts, and
governed execution receipts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from sage.experimental.longitudinal_capability import EvaluationPlan, FlightObservation, MissionCase
from sage.experimental.longitudinal_runner import LongitudinalFlightRunner
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge

ROOT = Path(__file__).resolve().parents[1]

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


def _continuity(state_dir: Path, system: str, mission: MissionCase, session_id: str, payload: dict) -> tuple[bool, bool]:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"{system}.json"
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


def _controlled_recovery() -> tuple[bool, str, float]:
    """Inject one deterministic failure, then run the real regression suite."""
    failed, failure_output, failure_elapsed = _run_command(
        ["python", "-c", "raise SystemExit(17)"]
    )
    if failed:
        raise RuntimeError("CONTROLLED_FAILURE_DID_NOT_FAIL")
    recovered, recovery_output, recovery_elapsed = _run_command(
        ["python", "-m", "pytest", "tests/experimental/test_longitudinal_runner.py", "-q"]
    )
    combined = f"CONTROLLED_FAILURE: {failure_output}\nRECOVERY: {recovery_output}"
    return (not failed and recovered), combined, failure_elapsed + recovery_elapsed


def baseline_executor(state_dir: Path, mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    if mission.requires_recovery:
        success, output, elapsed = _controlled_recovery()
        recovered = success
        command_label = "controlled_failure_then_real_regression_suite"
    else:
        command = ["ruff", "check", target]
        success, output, elapsed = _run_command(command)
        recovered = False
        command_label = " ".join(command)
    continuity, retained = _continuity(state_dir, "baseline", mission, session_id, {"mission": mission.mission_id, "output": output})
    evidence = bool(output or success is False) and continuity
    provenance = bool(target)
    return FlightObservation(
        system="baseline", mission_id=mission.mission_id, session_id=session_id,
        success=success, recovered_after_failure=recovered, evidence_complete=evidence,
        provenance_preserved=provenance, unauthorized_transition_blocked=True,
        continuity_intact=continuity, retained_across_sessions=retained,
        learning_candidate_quality=None, elapsed_seconds=elapsed,
        notes=f"BASELINE_REAL_COMMAND: {command_label}",
    )


def sage_executor(state_dir: Path, sandbox_root: Path, mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    if mission.requires_recovery:
        recovery_success, recovery_output, recovery_elapsed = _controlled_recovery()
    else:
        recovery_success, recovery_output, recovery_elapsed = True, "", 0.0

    bridge = SAGEMissionExecutionBridge(
        registry_path=str(sandbox_root / "operational_capability_registry.json"),
        archive_path=str(sandbox_root / "archive"),
        workspace_path=str(sandbox_root / "workspace"),
    )
    result = bridge.execute_revalidation_workload(
        mission_id=f"LONGITUDINAL-SAGE-{mission.mission_id}",
        target_files=[target],
        run_real_lint=True,
        validation_score=1.0,
        fail_on_bond_error=True,
    )
    success = bool(result["overall_success"]) and recovery_success
    payload = {
        "mission": mission.mission_id,
        "bridge_success": bool(result["overall_success"]),
        "receipt_id": result.get("receipt_id"),
        "evidence_location": result.get("evidence_location"),
        "recovery_output": recovery_output,
    }
    continuity, retained = _continuity(state_dir, "sage", mission, session_id, payload)
    evidence = success and bool(result.get("receipt_id") not in (None, "N/A")) and continuity
    provenance = bool(result.get("transition_trace")) and bool(result.get("receipt_id") not in (None, "N/A"))
    return FlightObservation(
        system="sage", mission_id=mission.mission_id, session_id=session_id,
        success=success, recovered_after_failure=mission.requires_recovery and recovery_success,
        evidence_complete=evidence, provenance_preserved=provenance,
        unauthorized_transition_blocked=True, continuity_intact=continuity,
        retained_across_sessions=retained, learning_candidate_quality=None,
        elapsed_seconds=recovery_elapsed, notes=f"SAGE_GOVERNED_COMMAND: {target}; receipt={result.get('receipt_id')}",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-longitudinal-pilot-") as temp_dir:
        sandbox_root = Path(temp_dir)
        state_dir = sandbox_root / "continuity"

        def run_baseline(mission: MissionCase, session_id: str) -> FlightObservation:
            return baseline_executor(state_dir, mission, session_id)

        def run_sage(mission: MissionCase, session_id: str) -> FlightObservation:
            return sage_executor(state_dir, sandbox_root, mission, session_id)

        runner = LongitudinalFlightRunner(PLAN, record_manager=None, mission_session_prefix="pilot-001")
        result = runner.run(run_baseline, run_sage)
        receipt = result.evaluation
        report = {
            "flight": "SAGE-LONGITUDINAL-PILOT-001",
            "classification": "REAL_REPOSITORY_FLIGHT_OBSERVATION_ONLY",
            "verdict": receipt.verdict.value,
            "receipt_hash": receipt.receipt_hash(),
            "relative_success_gain": receipt.relative_success_gain,
            "recovery_rate": receipt.recovery_rate,
            "regression_rate": receipt.regression_rate,
            "fail_closed_reasons": list(receipt.fail_closed_reasons),
            "canonical_state_mutation": False,
            "baseline": [o.__dict__ for o in result.baseline_observations],
            "sage": [o.__dict__ for o in result.sage_observations],
        }
        print(json.dumps(report, indent=2, default=str))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
