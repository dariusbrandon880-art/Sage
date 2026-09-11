"""Unit and integration tests for AIET Validation Lab (sage/experimental/aiet)."""

import json
import pytest

from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet import (
    AIETBlindScenario,
    AIETControlAdapter,
    AIETIndependentEvaluator,
    AIETMetricsCalculator,
    AIETMissionRunner,
    AIETPerturbationInjector,
    AIETValidationReceipt,
    FailurePerturbation,
)
from sage.experimental.aiet.perturbation import PerturbationType


def test_aiet_scenario_invariants():
    scenario = AIETBlindScenario(
        scenario_id="scenario_001",
        description="Test Blind Scenario",
        domain="C2_TEST",
        expected_invariants=["KEY_EXISTS:result", "NON_EMPTY:status", "GTE:score:0.80"],
    )

    valid_output = {"result": "ok", "status": "active", "score": 0.85}
    passed, violations = scenario.validate_invariants(valid_output)
    assert passed is True
    assert len(violations) == 0

    invalid_output = {"status": "", "score": 0.70}
    passed_inv, violations_inv = scenario.validate_invariants(invalid_output)
    assert passed_inv is False
    assert "MISSING_KEY:result" in violations_inv
    assert "EMPTY_VALUE:status" in violations_inv
    assert "INVARIANT_BELOW_THRESHOLD:score<0.8" in violations_inv


def test_aiet_perturbation_injector():
    perturbation = FailurePerturbation(
        perturbation_id="pert_noise_01",
        perturbation_type=PerturbationType.INPUT_NOISE,
        severity=0.5,
        target_key="input_data",
    )
    injector = AIETPerturbationInjector([perturbation])

    inputs = {"input_data": "canonical_payload", "param": 100}
    modified_inputs, logs = injector.apply(inputs)

    assert "canonical_payload_NOISE_50" in modified_inputs["input_data"]
    assert "INJECTED_NOISE:input_data" in logs


def test_aiet_metrics_calculator():
    base_fit = FitnessVector(mission_value=0.6, correctness=0.6, repeatability=0.6, evidence_quality=0.6, recovery=0.6, generalization=0.6, cost=1.0)
    cand_fit = FitnessVector(mission_value=0.9, correctness=0.95, repeatability=0.9, evidence_quality=0.9, recovery=0.9, generalization=0.9, cost=0.8)
    pert_fit = FitnessVector(mission_value=0.8, correctness=0.85, repeatability=0.8, evidence_quality=0.8, recovery=0.85, generalization=0.8, cost=0.9)
    trans_fit = FitnessVector(mission_value=0.85, correctness=0.9, repeatability=0.85, evidence_quality=0.85, recovery=0.85, generalization=0.85, cost=0.8)

    metrics = AIETMetricsCalculator.calculate_metrics(
        baseline_fitness=base_fit,
        candidate_fitness=cand_fit,
        perturbed_candidate_fitness=pert_fit,
        transfer_fitness=trans_fit,
        regression_free=True,
    )

    assert metrics.adaptation_gain > 0.0
    assert 0.0 <= metrics.recovery_rate <= 1.0
    assert 0.0 <= metrics.transfer_efficiency <= 1.0
    assert 0.0 <= metrics.resilience_score <= 1.0


def test_aiet_runner_validation_flight():
    contract = MissionContract.from_mapping({
        "schema_version": "1.0",
        "mission_id": "aiet_mission_test",
        "intent": "Test AIET mission contract binding",
        "authority_boundary": {
            "allowed_paths": ["sage/experimental/aiet/**"],
            "prohibited_paths": ["sage/runtime/**"],
        },
        "completion_criteria": {
            "required_tests": ["tests/experimental/test_aiet_validation.py"],
            "provenance_required": True,
        },
    })

    scenarios = [
        AIETBlindScenario(
            scenario_id="scenario_alpha",
            description="Alpha blind task",
            domain="SYNTHESIS",
            inputs={"query": "test_alpha"},
            expected_invariants=["KEY_EXISTS:status"],
            transfer_target_domain="ANALYSIS",
        )
    ]

    perturbations = [
        FailurePerturbation(
            perturbation_id="pert_drift_01",
            perturbation_type=PerturbationType.ENVIRONMENT_DRIFT,
            severity=0.2,
        )
    ]

    def baseline_executor(inputs):
        return {"status": "ok", "mission_value": 0.6, "repeatability": 0.7, "recovery_rate": 0.6}

    def candidate_executor(inputs):
        return {"status": "ok", "mission_value": 0.9, "repeatability": 0.95, "recovery_rate": 0.9}

    runner = AIETMissionRunner()
    receipt = runner.run_validation_flight(
        mission_contract=contract,
        scenarios=scenarios,
        baseline_executor=baseline_executor,
        candidate_executor=candidate_executor,
        perturbations=perturbations,
        baseline_technique_id="base_v1",
        candidate_technique_id="cand_v2",
    )

    assert isinstance(receipt, AIETValidationReceipt)
    assert receipt.mission_id == "aiet_mission_test"
    assert receipt.trials_count == 4
    assert receipt.overall_verdict == "PASS"
    assert receipt.evolution_decision == "PROMOTE_CANDIDATE"
    assert len(receipt.git_head_sha) == 40

    payload = receipt.to_dict()
    assert "receipt_hash" in payload
    assert len(payload["receipt_hash"]) == 64
