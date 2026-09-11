"""AIET Validation Lab harness execution.

This script validates the harness plumbing with deterministic fixtures. It deliberately
cannot produce an autonomy verdict. Real AIET evidence requires an externally bounded
executor and independent harness/evaluator proof.
"""

from __future__ import annotations

import json
from pathlib import Path

from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet import AIETBlindScenario, AIETMissionRunner, AIETValidationReceipt, FailurePerturbation
from sage.experimental.aiet.perturbation import PerturbationType


def execute_aiet_validation_lab() -> AIETValidationReceipt:
    contract = MissionContract.from_mapping({
        "schema_version": "1.0",
        "mission_id": "aiet_frozen_trials_wave_2026",
        "intent": "Validate AIET harness mechanics without claiming autonomous intelligence",
        "authority_boundary": {
            "allowed_paths": [
                "sage/experimental/aiet/**",
                "evidence_capture/aiet_validation_receipt.json",
                "scripts/execute_aiet_validation.py",
                "tests/experimental/test_aiet_validation.py",
            ],
            "prohibited_paths": ["sage/runtime/**", "sage/core/**"],
        },
        "completion_criteria": {
            "required_tests": ["tests/experimental/test_aiet_validation.py"],
            "min_coverage_pct": 90.0,
            "provenance_required": True,
        },
        "metadata": {
            "target_paths": [
                "sage/experimental/aiet/runner.py",
                "sage/experimental/aiet/evaluator.py",
            ]
        },
    })

    scenarios = [
        AIETBlindScenario(
            scenario_id="blind_scenario_01_recon_synthesis",
            description="Blind reconnaissance and capability graph synthesis under drift",
            domain="RECONNAISSANCE",
            difficulty_level="MAJOR",
            inputs={"target_nodes": 143, "query_depth": 3, "expected_seams": 7},
            expected_invariants=["KEY_EXISTS:status", "NON_EMPTY:synthesis_digest", "GTE:score:0.85"],
            transfer_target_domain="GOVERNANCE_AUDIT",
        ),
        AIETBlindScenario(
            scenario_id="blind_scenario_02_continuity_recovery",
            description="Rehydration checkpoint validation and session recovery under state corruption",
            domain="CONTINUITY",
            difficulty_level="CRITICAL",
            inputs={"session_id": "sess_aiet_2026", "checkpoint_depth": 5},
            expected_invariants=["KEY_EXISTS:status", "NON_EMPTY:checkpoint_hash", "GTE:score:0.80"],
            transfer_target_domain="DISASTER_RECOVERY",
        ),
    ]

    perturbations = [
        FailurePerturbation(
            perturbation_id="pert_01_input_noise",
            perturbation_type=PerturbationType.INPUT_NOISE,
            severity=0.4,
            target_key="session_id",
        ),
        FailurePerturbation(
            perturbation_id="pert_02_environment_drift",
            perturbation_type=PerturbationType.ENVIRONMENT_DRIFT,
            severity=0.25,
        ),
    ]

    # Deterministic fixtures prove only that the five-phase harness can execute and
    # persist evidence. They are intentionally marked as non-external execution.
    def baseline_executor(inputs: dict) -> dict:
        return {
            "status": "COMPLETED",
            "synthesis_digest": "fixture_baseline_digest",
            "checkpoint_hash": "fixture_baseline_checkpoint",
            "score": 0.82,
            "mission_value": 0.70,
            "repeatability": 0.80,
            "evidence_quality": 0.75,
            "recovery_rate": 0.65,
            "generalization": 0.70,
        }

    def candidate_executor(inputs: dict) -> dict:
        drift = float(inputs.get("_drift_factor", 0.0))
        return {
            "status": "COMPLETED",
            "synthesis_digest": "fixture_candidate_digest",
            "checkpoint_hash": "fixture_candidate_checkpoint",
            "score": round(max(0.0, 0.95 - drift * 0.2), 2),
            "mission_value": round(min(1.0, 0.95 - drift * 0.1), 2),
            "repeatability": 0.95,
            "evidence_quality": 0.95,
            "recovery_rate": round(max(0.0, 0.92 - drift * 0.1), 2),
            "generalization": 0.90,
        }

    receipt = AIETMissionRunner().run_validation_flight(
        mission_contract=contract,
        scenarios=scenarios,
        baseline_executor=baseline_executor,
        candidate_executor=candidate_executor,
        perturbations=perturbations,
        baseline_technique_id="fixture_baseline_v1",
        candidate_technique_id="fixture_candidate_v2",
        execution_mode="fixture",
    )

    output_path = Path("evidence_capture/aiet_validation_receipt.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt.to_dict(), indent=2) + "\n", encoding="utf-8")

    print(f"AIET harness verdict: {receipt.overall_verdict}")
    print(f"Trials executed: {receipt.trials_count}")
    print(f"Evidence receipt: {output_path}")
    print("NOTE: fixture execution is not evidence of autonomous intelligence.")
    return receipt


if __name__ == "__main__":
    receipt = execute_aiet_validation_lab()
    if receipt.overall_verdict == "INVALID_EXPERIMENT":
        raise SystemExit(1)
