"""Launch-readiness tests for the AIET external harness."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet import (
    AIETBlindScenario,
    AIETExternalClient,
    AIETExternalClientError,
    AIETExternalHarnessServer,
    AIETExternalServerError,
    AIETMetricsCalculator,
    AIETMissionRunner,
    AIETProviderAdapter,
    AIETProviderConfig,
    AIETValidationReceipt,
    FailurePerturbation,
)
from sage.experimental.aiet.perturbation import PerturbationType

TARGET_SHA = "a" * 40


def _contract(mission_id="aiet_test"):
    return {
        "schema_version": "1.0",
        "mission_id": mission_id,
        "intent": "AIET external harness launch-readiness verification",
        "authority_boundary": {"allowed_paths": ["sage/experimental/aiet/**"], "prohibited_paths": ["sage/runtime/**", "sage/core/**"]},
        "completion_criteria": {"provenance_required": True},
    }


def test_scenario_invariants():
    scenario = AIETBlindScenario(scenario_id="s", description="d", domain="TEST", expected_invariants=["KEY_EXISTS:result", "NON_EMPTY:status"])
    assert scenario.validate_invariants({"result": "ok", "status": "active"}) == (True, [])
    passed, violations = scenario.validate_invariants({"status": ""})
    assert not passed and "MISSING_KEY:result" in violations and "EMPTY_VALUE:status" in violations


def test_perturbation_injector():
    p = FailurePerturbation(perturbation_id="p", perturbation_type=PerturbationType.INPUT_NOISE, severity=.5, target_key="x")
    changed, logs = __import__("sage.experimental.aiet.perturbation", fromlist=["AIETPerturbationInjector"]).AIETPerturbationInjector([p]).apply({"x": "value"})
    assert changed["x"] == "value_NOISE_50" and logs == ["INJECTED_NOISE:x"]


def test_independent_evaluator_caps_gaming():
    from sage.experimental.aiet.evaluator import AIETIndependentEvaluator
    scenario = AIETBlindScenario(scenario_id="s", description="d", domain="SECURITY", expected_invariants=["KEY_EXISTS:required"])
    fit, violations = AIETIndependentEvaluator().evaluate_run(scenario, {"mission_value": 1, "repeatability": 1, "evidence_quality": 1, "recovery_rate": 1, "generalization": 1}, .1)
    assert violations and fit.correctness == .75 and fit.mission_value <= .75


def test_metrics_calculator():
    b = FitnessVector(.6, .6, .6, .6, .6, .6, 1)
    c = FitnessVector(.9, .95, .9, .9, .9, .9, .8)
    p = FitnessVector(.8, .85, .8, .8, .85, .8, .9)
    t = FitnessVector(.85, .9, .85, .85, .85, .85, .8)
    m = AIETMetricsCalculator.calculate_metrics(b, c, p, t, True)
    assert m.adaptation_gain > 0 and 0 <= m.resilience_score <= 1


def test_runner_fixture_fails_closed():
    scenario = AIETBlindScenario(scenario_id="s", description="d", domain="TEST", inputs={"q": "x"}, expected_invariants=["KEY_EXISTS:status"])
    receipt = AIETMissionRunner().run_validation_flight(
        mission_contract=MissionContract.from_mapping(_contract()), scenarios=[scenario],
        baseline_executor=lambda _: {"status": "ok"}, candidate_executor=lambda _: {"status": "ok"},
        perturbations=[], baseline_technique_id="b", candidate_technique_id="c", execution_mode="fixture")
    assert receipt.overall_verdict == "AUTOMATION" and "NON_EXTERNAL_EXECUTION:fixture" in receipt.fail_closed_reasons


def test_external_client_refuses_fixture():
    client = AIETExternalClient(harness_url="https://example.invalid", harness_key="k")
    with pytest.raises(AIETExternalClientError, match="INVALID_EXECUTION_MODE"):
        client.initiate_flight(MissionContract.from_mapping(_contract()), AIETProviderConfig(provider_name="openai", model_name="gpt-test"), execution_mode="fixture")


def test_provider_missing_secret(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AIETExternalServerError, match="MISSING_PROVIDER_CREDENTIALS"):
        AIETProviderAdapter.resolve_provider_credentials(AIETProviderConfig(provider_name="openai", model_name="gpt-test"))


def test_provider_invocation_hits_real_http_endpoint(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length))
            assert body["model"] == "gpt-test"
            payload = {"id": "real-http-1", "choices": [{"message": {"content": "live provider response"}}]}
            data = json.dumps(payload).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self, *_): return
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler); threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    try:
        result = AIETProviderAdapter.invoke_provider(AIETProviderConfig(provider_name="openai", model_name="gpt-test"), {"_trial_phase": "BASELINE_DISCOVERY"})
        assert result["result"] == "live provider response"
        assert result["raw_provider_response"]["id"] == "real-http-1"
        assert result["synthesis_digest"] != ""
        assert "mission_value" not in result
    finally:
        server.shutdown()


def test_actual_out_of_band_disruption_and_recovery(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(503); self.end_headers()
        def do_POST(self):  # noqa: N802
            payload = {"id": "recovered", "choices": [{"message": {"content": "recovered provider response"}}]}
            data = json.dumps(payload).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self, *_): return
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler); threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("SAGE_AIET_DISRUPTION_URL", f"http://127.0.0.1:{server.server_port}/fail")
    try:
        result = AIETProviderAdapter.invoke_provider(AIETProviderConfig(provider_name="openai", model_name="gpt-test"), {"_trial_phase": "ACTIVE_DISRUPTION"}, induce_disruption=True)
        assert result["disruption_encountered"] is True
        assert "HTTP 503" in result["disruption_error"]
        assert result["result"] == "recovered provider response"
    finally:
        server.shutdown()


def test_server_requires_target_sha(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    server = AIETExternalHarnessServer(secret_harness_key="secret")
    with pytest.raises(AIETExternalServerError, match="INVALID_TARGET_GIT_SHA"):
        server.initiate_flight(_contract(), {"provider_name": "openai", "model_name": "gpt-test"}, provided_harness_key="secret")


def test_server_rejects_target_sha_mismatch(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key"); monkeypatch.setenv("SAGE_AIET_TARGET_GIT_SHA", "b" * 40)
    server = AIETExternalHarnessServer(secret_harness_key="secret")
    with pytest.raises(AIETExternalServerError, match="TARGET_GIT_SHA_MISMATCH"):
        server.initiate_flight(_contract(), {"provider_name": "openai", "model_name": "gpt-test"}, target_git_head_sha=TARGET_SHA, provided_harness_key="secret")


def test_health_endpoint():
    from sage.experimental.aiet.server import create_aiet_harness_app
    response = TestClient(create_aiet_harness_app()).get("/health")
    assert response.status_code == 200 and response.json() == {"status": "healthy", "service": "sage-aiet-harness"}


def test_end_to_end_receipt_sha_binding_and_hash(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    server = AIETExternalHarnessServer(secret_harness_key="secret")
    def transport(config, inputs, disruption):
        return {"status": "COMPLETED", "result": "candidate output", "synthesis_digest": "digest-" + inputs["_trial_phase"], "checkpoint_hash": "checkpoint-" + inputs["_trial_phase"], "raw_provider_response": {"provider": config.provider_name, "phase": inputs["_trial_phase"]}}
    init = server.initiate_flight(_contract("e2e"), {"provider_name": "openai", "model_name": "gpt-test"}, target_git_head_sha=TARGET_SHA, provided_harness_key="secret")
    receipt_data = server.execute_flight(init["flight_id"], provided_harness_key="secret", custom_http_handler=transport)
    receipt = AIETExternalClient.validate_remote_receipt(receipt_data, expected_target_sha=TARGET_SHA)
    assert receipt.git_head_sha == TARGET_SHA and receipt.human_intervention_count == 0 and len(receipt.evidence_proof_hash) == 64


def test_receipt_tamper_and_fixture_rejection():
    receipt = AIETValidationReceipt(receipt_id="r", mission_id="m", trials_count=1, scenarios_evaluated=["s"], perturbations_injected=[], baseline_technique_id="b", candidate_technique_id="c", adaptation_gain=0, recovery_rate=0, transfer_efficiency=0, resilience_score=0, evolution_decision="HOLD", overall_verdict="PARTIAL_AUTONOMY", isolation_status="REQUIRES_HARNESS_PROOF", initial_state_hash="a" * 64, scenario_hash="b" * 64, constraint_integrity=True, verification_integrity=True, human_intervention_count=0, unscripted_discovery=True, adaptation_latency_steps=0, final_state_hash="c" * 64, verdict="PARTIAL_AUTONOMY", execution_mode="external", git_head_sha=TARGET_SHA)
    data = receipt.to_dict(); data["resilience_score"] = .99
    with pytest.raises(AIETExternalClientError, match="RECEIPT_HASH_MISMATCH"):
        AIETExternalClient.validate_remote_receipt(data)
    fixture = receipt.to_dict(); fixture["execution_mode"] = "fixture"; fixture["evidence_proof_hash"] = AIETValidationReceipt(**fixture).compute_hash()
    with pytest.raises(AIETExternalClientError, match="INVALID_EXTERNAL_RECEIPT"):
        AIETExternalClient.validate_remote_receipt(fixture)
