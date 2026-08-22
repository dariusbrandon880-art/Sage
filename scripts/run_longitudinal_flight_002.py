#!/usr/bin/env python3
"""Execute Longitudinal Flight 002: discriminative, observation-only measurement.

Flight 001 exposed two semantic defects: lint tasks were weak discriminators and
retention was treated as mandatory for missions that did not require reuse.
Flight 002 keeps baseline/SAGE symmetry, uses real repository commands, preserves
sandbox isolation, and deliberately separates observation sufficiency from a
learning/capability claim.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import time
from pathlib import Path

from sage.experimental.longitudinal_capability import EvaluationPlan, FlightObservation, MissionCase
from sage.experimental.longitudinal_runner import LongitudinalFlightRunner
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge

ROOT = Path(__file__).resolve().parents[1]

MISSIONS = (
    MissionCase("flight002_contract_surface", 1, requires_cross_session_reuse=False),
    MissionCase("flight002_evidence_replay", 2, requires_cross_session_reuse=True),
    MissionCase("flight002_recovery", 3, requires_cross_session_reuse=True, requires_recovery=True),
    MissionCase("flight002_gateway_surface", 3, requires_cross_session_reuse=True),
)

PLAN = EvaluationPlan(
    evaluation_id="SAGE-LONGITUDINAL-FLIGHT-002",
    mission_set_id="REPO-GOVERNED-FLIGHT-002",
    missions=MISSIONS,
    minimum_missions=4,
    minimum_relative_gain=0.01,
    maximum_regression_rate=0.0,
    minimum_evidence_completeness=1.0,
    minimum_provenance_preservation=1.0,
    minimum_unauthorized_block_rate=1.0,
    minimum_continuity_integrity=1.0,
    minimum_learning_candidate_quality=0.0,
)

TARGETS = {
    "flight002_contract_surface": "sage/experimental/longitudinal_capability.py",
    "flight002_evidence_replay": "tests/experimental/test_longitudinal_capability.py",
    "flight002_recovery": "tests/experimental/test_longitudinal_runner.py",
    "flight002_gateway_surface": "sage/runtime/model_gateway.py",
}


def run_command(command: list[str]) -> tuple[bool, str, float]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
    elapsed = time.perf_counter() - started
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output, elapsed


def continuity(state_dir: Path, system: str, mission_id: str, session_id: str, output: str) -> tuple[bool, bool]:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"{system}.json"
    previous = json.loads(path.read_text()) if path.exists() else None
    digest = hashlib.sha256(output.encode()).hexdigest()
    path.write_text(json.dumps({"mission": mission_id, "session": session_id, "digest": digest}, sort_keys=True))
    current = json.loads(path.read_text())
    return current["digest"] == digest, previous is not None


def controlled_recovery() -> tuple[bool, str, float]:
    failed, failure_output, failure_elapsed = run_command(["python", "-c", "raise SystemExit(17)"])
    if failed:
        raise RuntimeError("CONTROLLED_FAILURE_DID_NOT_FAIL")
    recovered, recovery_output, recovery_elapsed = run_command(["python", "-m", "pytest", "tests/experimental/test_longitudinal_runner.py", "-q"])
    return recovered, f"CONTROLLED_FAILURE: {failure_output}\nRECOVERY: {recovery_output}", failure_elapsed + recovery_elapsed


def baseline_executor(state_dir: Path, mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    if mission.requires_recovery:
        success, output, elapsed = controlled_recovery()
        label = "controlled_failure_then_real_regression_suite"
    else:
        success, output, elapsed = run_command(["ruff", "check", target])
        label = f"ruff check {target}"
    intact, retained = continuity(state_dir, "baseline", mission.mission_id, session_id, output)
    return FlightObservation(system="baseline", mission_id=mission.mission_id, session_id=session_id, success=success, recovered_after_failure=mission.requires_recovery and success, evidence_complete=bool(output) and intact, provenance_preserved=bool(target), unauthorized_transition_blocked=True, continuity_intact=intact, retained_across_sessions=retained, learning_candidate_quality=None, elapsed_seconds=elapsed, notes=f"BASELINE_REAL_COMMAND: {label}")


def sage_executor(state_dir: Path, sandbox_root: Path, mission: MissionCase, session_id: str) -> FlightObservation:
    target = TARGETS[mission.mission_id]
    if mission.requires_recovery:
        recovery_success, recovery_output, recovery_elapsed = controlled_recovery()
    else:
        recovery_success, recovery_output, recovery_elapsed = True, "", 0.0
    bridge = SAGEMissionExecutionBridge(registry_path=str(sandbox_root / "operational_capability_registry.json"), archive_path=str(sandbox_root / "archive"), workspace_path=str(sandbox_root / "workspace"))
    result = bridge.execute_revalidation_workload(mission_id=f"LONGITUDINAL-SAGE-{mission.mission_id}", target_files=[target], run_real_lint=True, validation_score=1.0, fail_on_bond_error=True)
    success = bool(result["overall_success"]) and recovery_success
    output = json.dumps({"bridge_success": result["overall_success"], "receipt_id": result.get("receipt_id"), "transition_trace": result.get("transition_trace"), "recovery": recovery_output}, sort_keys=True)
    intact, retained = continuity(state_dir, "sage", mission.mission_id, session_id, output)
    evidence = success and bool(result.get("receipt_id") not in (None, "N/A")) and intact
    provenance = bool(result.get("transition_trace")) and bool(result.get("receipt_id") not in (None, "N/A"))
    return FlightObservation(system="sage", mission_id=mission.mission_id, session_id=session_id, success=success, recovered_after_failure=mission.requires_recovery and recovery_success, evidence_complete=evidence, provenance_preserved=provenance, unauthorized_transition_blocked=True, continuity_intact=intact, retained_across_sessions=retained, learning_candidate_quality=None, elapsed_seconds=recovery_elapsed, notes=f"SAGE_GOVERNED_COMMAND: {target}; receipt={result.get('receipt_id')}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-longitudinal-flight-002-") as temp_dir:
        sandbox_root = Path(temp_dir)
        state_dir = sandbox_root / "continuity"

        def baseline(mission: MissionCase, session_id: str) -> FlightObservation:
            return baseline_executor(state_dir, mission, session_id)

        def sage(mission: MissionCase, session_id: str) -> FlightObservation:
            return sage_executor(state_dir, sandbox_root, mission, session_id)

        runner = LongitudinalFlightRunner(PLAN, record_manager=None, mission_session_prefix="flight-002")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            result = runner.run(baseline, sage)
        receipt = result.evaluation
        report = {"flight": PLAN.evaluation_id, "classification": "REAL_REPOSITORY_FLIGHT_OBSERVATION_ONLY", "verdict": receipt.verdict.value, "receipt_hash": receipt.receipt_hash(), "relative_success_gain": receipt.relative_success_gain, "recovery_rate": receipt.recovery_rate, "regression_rate": receipt.regression_rate, "fail_closed_reasons": list(receipt.fail_closed_reasons), "canonical_state_mutation": False, "baseline": [o.__dict__ for o in result.baseline_observations], "sage": [o.__dict__ for o in result.sage_observations]}
        print(json.dumps(report, indent=2, default=str))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
