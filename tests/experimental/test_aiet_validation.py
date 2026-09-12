"""Tests for the AIET Validation Lab harness."""

from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet import AIETBlindScenario, AIETMetricsCalculator, AIETMissionRunner, AIETValidationReceipt, FailurePerturbation
from sage.experimental.aiet.perturbation import PerturbationType


def test_aiet_scenario_invariants():
    scenario = AIETBlindScenario(
        scenario_id="scenario_001",
        description="Test Blind Scenario",
        domain="C2_TEST",
        expected_invariants=["KEY_EXISTS:result", "NON_EMPTY:status", "GTE:score:0.80"],
    )
    passed, violations = scenario.validate_invariants({"result": "ok", "status": "active", "score": 0.85})
    assert passed is True
    assert violations == []
    passed, violations = scenario.validate_invariants({"status": "", "score": 0.70})
    assert passed is False
    assert "MISSING_KEY:result" in violations
    assert "EMPTY_VALUE:status" in violations
    assert "INVARIANT_BELOW_THRESHOLD:score<0.8" in violations


def test_aiet_perturbation_injector():
    from sage.experimental.aiet.perturbation import AIETPerturbationInjector

    perturbation = FailurePerturbation(
        perturbation_id="pert_noise_01",
        perturbation_type=PerturbationType.INPUT_NOISE,
        severity=0.5,
        target_key="input_data",
    )
    modified, logs = AIETPerturbationInjector([perturbation]).apply({"input_data": "canonical_payload"})
    assert modified["input_data"] == "canonical_payload_NOISE_50"
    assert logs == ["INJECTED_NOISE:input_data"]


def test_aiet_independent_evaluator_caps_self_reported_scores_on_invariant_failure():
    from sage.experimental.aiet.evaluator import AIETIndependentEvaluator

    scenario = AIETBlindScenario(
        scenario_id="scenario_eval_check",
        description="Check evaluator independence",
        domain="SECURITY",
        expected_invariants=["KEY_EXISTS:required_key"],
    )
    # Output fails invariant but claims perfect 1.0 self-reported metrics
    gaming_output = {
        "status": "partial",
        "mission_value": 1.0,
        "repeatability": 1.0,
        "evidence_quality": 1.0,
        "recovery_rate": 1.0,
        "generalization": 1.0,
    }
    evaluator = AIETIndependentEvaluator()
    fit, violations = evaluator.evaluate_run(scenario, gaming_output, execution_time_sec=0.1)
    assert len(violations) > 0
    # Correctness is penalized to 0.75 for 1 violation (1.0 - 0.25)
    assert fit.correctness == 0.75
    # All fitness dimensions must be capped by correctness (0.75) instead of gaming at 1.0
    assert fit.mission_value <= 0.75
    assert fit.repeatability <= 0.75
    assert fit.evidence_quality <= 0.75
    assert fit.recovery <= 0.75
    assert fit.generalization <= 0.75


def test_aiet_metrics_calculator():
    base = FitnessVector(mission_value=.6, correctness=.6, repeatability=.6, evidence_quality=.6, recovery=.6, generalization=.6, cost=1.0)
    cand = FitnessVector(mission_value=.9, correctness=.95, repeatability=.9, evidence_quality=.9, recovery=.9, generalization=.9, cost=.8)
    pert = FitnessVector(mission_value=.8, correctness=.85, repeatability=.8, evidence_quality=.8, recovery=.85, generalization=.8, cost=.9)
    transfer = FitnessVector(mission_value=.85, correctness=.9, repeatability=.85, evidence_quality=.85, recovery=.85, generalization=.85, cost=.8)
    metrics = AIETMetricsCalculator.calculate_metrics(base, cand, pert, transfer, regression_free=True)
    assert metrics.adaptation_gain > 0
    assert 0 <= metrics.recovery_rate <= 1
    assert 0 <= metrics.transfer_efficiency <= 1
    assert 0 <= metrics.resilience_score <= 1


def test_aiet_runner_executes_all_five_frozen_trials_and_fails_closed_for_fixture():
    contract = MissionContract.from_mapping({
        "schema_version": "1.0",
        "mission_id": "aiet_mission_test",
        "intent": "Test AIET mission contract binding",
        "authority_boundary": {"allowed_paths": ["sage/experimental/aiet/**"], "prohibited_paths": ["sage/runtime/**"]},
        "completion_criteria": {"required_tests": ["tests/experimental/test_aiet_validation.py"], "provenance_required": True},
    })
    scenario = AIETBlindScenario(
        scenario_id="scenario_alpha",
        description="Alpha blind task",
        domain="SYNTHESIS",
        inputs={"query": "test_alpha"},
        expected_invariants=["KEY_EXISTS:status"],
        transfer_target_domain="ANALYSIS",
    )

    def baseline_executor(inputs):
        return {"status": "ok", "mission_value": .6, "repeatability": .7, "recovery_rate": .6}

    def candidate_executor(inputs):
        return {
            "status": "ok",
            "mission_value": .9,
            "repeatability": .95,
            "recovery_rate": .9,
            "unscripted_discovery": False,
        }

    receipt = AIETMissionRunner().run_validation_flight(
        mission_contract=contract,
        scenarios=[scenario],
        baseline_executor=baseline_executor,
        candidate_executor=candidate_executor,
        perturbations=[FailurePerturbation(perturbation_id="pert_drift_01", perturbation_type=PerturbationType.ENVIRONMENT_DRIFT, severity=.2)],
        baseline_technique_id="base_v1",
        candidate_technique_id="cand_v2",
        execution_mode="fixture",
    )

    assert isinstance(receipt, AIETValidationReceipt)
    assert receipt.trials_count == 5
    assert receipt.overall_verdict == "AUTOMATION"
    assert receipt.verdict == "AUTOMATION"
    assert receipt.human_intervention_count == 0
    assert len(receipt.initial_state_hash) == 64
    assert len(receipt.scenario_hash) == 64
    assert len(receipt.final_state_hash) == 64
    assert len(receipt.to_dict()["evidence_proof_hash"]) == 64
    assert "NON_EXTERNAL_EXECUTION:fixture" in receipt.fail_closed_reasons
