"""Tests for the AIET Validation Lab harness."""

import pytest
from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet import (
    AIETBlindScenario,
    AIETExternalClient,
    AIETExternalClientError,
    AIETMetricsCalculator,
    AIETMissionRunner,
    AIETProviderConfig,
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


def test_aiet_external_client_fails_closed_when_unconfigured():
    client = AIETExternalClient(harness_url="", harness_key="")
    assert client.is_configured() is False

    contract = MissionContract.from_mapping({
        "schema_version": "1.0",
        "mission_id": "test_unconfigured",
        "intent": "Unconfigured test",
        "completion_criteria": {"provenance_required": True},
    })
    provider = AIETProviderConfig(provider_name="openai", model_name="gpt-4o")

    with pytest.raises(AIETExternalClientError, match="EXTERNAL_HARNESS_NOT_CONFIGURED"):
        client.initiate_flight(contract, provider)

    with pytest.raises(AIETExternalClientError, match="EXTERNAL_HARNESS_NOT_CONFIGURED"):
        client.execute_flight("flight_123")

    with pytest.raises(AIETExternalClientError, match="EXTERNAL_HARNESS_NOT_CONFIGURED"):
        client.fetch_receipt("flight_123")


def test_aiet_external_client_refuses_fixture_execution_mode():
    client = AIETExternalClient(harness_url="https://aiet.external.org", harness_key="secret_key")
    contract = MissionContract.from_mapping({
        "schema_version": "1.0",
        "mission_id": "test_mode_check",
        "intent": "Refuse fixture test",
        "completion_criteria": {"provenance_required": True},
    })
    provider = AIETProviderConfig(provider_name="openai", model_name="gpt-4o")

    with pytest.raises(AIETExternalClientError, match="INVALID_EXECUTION_MODE"):
        client.initiate_flight(contract, provider, execution_mode="fixture")


def test_aiet_external_client_validates_remote_receipt_proof_hash_and_integrity():
    valid_receipt = AIETValidationReceipt(
        receipt_id="aiet_rcpt_ext_999",
        mission_id="aiet_mission_ext",
        trials_count=10,
        scenarios_evaluated=["scenario_1"],
        perturbations_injected=["pert_1"],
        baseline_technique_id="base_v1",
        candidate_technique_id="cand_v2",
        adaptation_gain=0.8,
        recovery_rate=0.85,
        transfer_efficiency=0.9,
        resilience_score=0.88,
        evolution_decision="PROMOTE",
        overall_verdict="DEMONSTRATED_AUTONOMOUS_ADAPTATION",
        isolation_status="REQUIRES_HARNESS_PROOF",
        initial_state_hash="a" * 64,
        scenario_hash="b" * 64,
        constraint_integrity=True,
        verification_integrity=True,
        human_intervention_count=0,
        unscripted_discovery=True,
        adaptation_latency_steps=1,
        final_state_hash="c" * 64,
        verdict="DEMONSTRATED_AUTONOMOUS_ADAPTATION",
        execution_mode="external",
        git_head_sha="668332be44af6bfbd2e39691dac388fc326bf1b9",
    )
    receipt_data = valid_receipt.to_dict()

    validated = AIETExternalClient.validate_remote_receipt(receipt_data)
    assert validated.receipt_id == "aiet_rcpt_ext_999"

    # Mismatched proof hash
    tampered_data = dict(receipt_data)
    tampered_data["resilience_score"] = 0.99
    with pytest.raises(AIETExternalClientError, match="RECEIPT_HASH_MISMATCH"):
        AIETExternalClient.validate_remote_receipt(tampered_data)

    # Remote receipt claiming fixture
    fixture_data = dict(receipt_data)
    fixture_data["execution_mode"] = "fixture"
    fixture_data["evidence_proof_hash"] = AIETValidationReceipt(**fixture_data).compute_hash()
    with pytest.raises(AIETExternalClientError, match="INVALID_EXTERNAL_RECEIPT"):
        AIETExternalClient.validate_remote_receipt(fixture_data)

    # Human intervention violation
    intervention_data = dict(receipt_data)
    intervention_data["human_intervention_count"] = 1
    intervention_data["evidence_proof_hash"] = AIETValidationReceipt(**intervention_data).compute_hash()
    with pytest.raises(AIETExternalClientError, match="HUMAN_INTERVENTION_VIOLATION"):
        AIETExternalClient.validate_remote_receipt(intervention_data)

    # Invalid git SHA
    bad_sha_data = dict(receipt_data)
    bad_sha_data["git_head_sha"] = "invalid_sha"
    bad_sha_data["evidence_proof_hash"] = AIETValidationReceipt(**bad_sha_data).compute_hash()
    with pytest.raises(AIETExternalClientError, match="INVALID_GIT_HEAD_SHA"):
        AIETExternalClient.validate_remote_receipt(bad_sha_data)
