import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS, CONTRACT_ID, CONTRACT_VERSION, DEEP_RECON_TRIGGERS,
    RECON_POLICY_PATH, REHYDRATION_SEQUENCE, REHYDRATION_TRIGGERS,
    classify_directive, render_system_contract, validate_report_claims,
)
from sage.c2.live_operation_receipt import LiveOperationReceipt, execute_live_capability, persist_live_operation_receipt, rehydrate_live_operation_receipt
from sage.runtime.model_adapters import OpenAIResponsesAdapter, _system_instructions
from sage.runtime.model_gateway import SAGEProtocolGovernor, SAGERuntime, SAGEStateSnapshot


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot("1", "sage-instance", "mission-1", "session-1", "authorized-frontier", "c2", "independent-verification")


class FakeLiveCapability:
    capability_id = "github"
    def __init__(self, *, target_resource="dariusbrandon880-art/Sage"):
        self.calls = []; self.target_resource = target_resource
    def invoke(self, *, operation: str, task: str):
        self.calls.append((operation, task))
        return {"target_resource": self.target_resource, "success": True, "result": {"head": "live-head", "operation": operation, "task": task}}


class FailedLiveCapability(FakeLiveCapability):
    def invoke(self, *, operation: str, task: str):
        self.calls.append((operation, task))
        return {"target_resource": self.target_resource, "success": False, "result": {"error": "live capability unavailable"}}


def structured_output(*, station="[SAGE::C2::CHATGPT]", claim="live repository verified"):
    return json.dumps({"station": station, "reasoning_chain": [claim], "proposed_actions": [], "epistemic_state": {"confidence_level": "HIGH"}, "evidence_refs": []})


def test_contract_contains_all_laws_and_identity():
    rendered = render_system_contract()
    assert CONTRACT_ID in rendered
    assert CONTRACT_VERSION == "1.6"
    assert len(ANTI_DRIFT_LAWS) == 18
    for law in ANTI_DRIFT_LAWS: assert law in rendered
    assert "Five flights is concurrent mission ownership across independent vehicles" in rendered
    assert "PREFLIGHT -> EXECUTE -> TEST -> EVIDENCE -> VERIFY -> RECONCILE -> REPORT" in rendered
    assert "SAGE is one governed organism with modular organs" in rendered


def test_deep_recon_policy_is_bound_and_has_velocity_language():
    rendered = render_system_contract()
    assert RECON_POLICY_PATH in rendered
    assert "REPOSITORY-FIRST REALITY LOCK" in rendered
    assert "TARGETED PRIMARY EXTERNAL INTELLIGENCE" in rendered
    assert "independent repository inspection and relevant external research may run concurrently" in rendered
    assert DEEP_RECON_TRIGGERS


def test_repo_truth_lock_requires_full_rehydration():
    decision = classify_directive("lock onto repo and whole repo truth")
    assert decision.requires_rehydration is True
    assert "lock onto repo" in decision.matched_rehydration_triggers
    assert "whole repo truth" in decision.matched_rehydration_triggers
    assert tuple(REHYDRATION_SEQUENCE) == ("REHYDRATE", "REALITY LOCK", "MISSION LOCK", "IDENTITY LOCK", "ACTIVE-FRONTIER LOCK")


def test_rehydrate_phrase_is_triggered_independently():
    decision = classify_directive("rehydrate C2")
    assert decision.requires_rehydration is True
    assert "rehydrate" in decision.matched_rehydration_triggers


def test_search_directive_requires_deep_recon_without_forcing_live_check():
    decision = classify_directive("Use Super Search and research the relevant engineering patterns")
    assert decision.requires_deep_recon is True
    assert "super search" in decision.matched_recon_triggers
    assert decision.requires_live_verification is False


def test_audit_directive_requires_deep_recon():
    decision = classify_directive("Perform a deep repo audit")
    assert decision.requires_deep_recon is True
    assert "audit" in decision.matched_recon_triggers


def test_live_check_directive_requires_live_verification():
    decision = classify_directive("Check live repo and inspect PR")
    assert decision.requires_live_verification is True
    assert "check live repo" in decision.matched_triggers
    assert "inspect pr" in decision.matched_triggers


def test_normal_directive_does_not_force_live_check(): assert classify_directive("Design five future research frontiers").requires_live_verification is False

def test_false_live_claim_fails_closed_without_receipt():
    with pytest.raises(ValueError, match="LiveOperationReceipt"): validate_report_claims(receipt=None, claim="Verified live repository state")

def test_boolean_cannot_substitute_for_receipt():
    with pytest.raises(ValueError, match="LiveOperationReceipt"): validate_report_claims(receipt=True, claim="Verified live repository state")

def test_live_claim_requires_bound_receipt_evidence():
    receipt = execute_live_capability(FakeLiveCapability(), operation="live_verification", task="check live repo")
    with pytest.raises(ValueError, match="not bound to response evidence"): validate_report_claims(receipt=receipt, claim="Verified live repository state", expected_target_resource=receipt.target_resource, evidence_refs=())

def test_live_claim_accepts_authentic_bound_receipt():
    receipt = execute_live_capability(FakeLiveCapability(), operation="live_verification", task="check live repo")
    validate_report_claims(receipt=receipt, claim="Verified live repository state", expected_target_resource=receipt.target_resource, evidence_refs=(receipt.receipt_hash,))

def test_tampered_receipt_fails_closed():
    receipt = execute_live_capability(FakeLiveCapability(), operation="live_verification", task="check live repo"); tampered = replace(receipt, target_resource="spoofed/repo")
    with pytest.raises(ValueError, match="invalid or failed receipt"): validate_report_claims(receipt=tampered, claim="Verified live repository state", expected_target_resource=receipt.target_resource, evidence_refs=(tampered.receipt_hash,))

def test_receipt_is_created_only_after_capability_invocation():
    capability = FakeLiveCapability(); receipt = execute_live_capability(capability, operation="live_verification", task="check live repo"); assert capability.calls == [("live_verification", "check live repo")]; assert isinstance(receipt, LiveOperationReceipt); assert receipt.verify(); assert receipt.success is True

def test_failed_live_capability_holds_execution():
    with pytest.raises(ValueError, match="operation failed"): execute_live_capability(FailedLiveCapability(), operation="live_verification", task="check live repo")

def test_persisted_receipt_rehydrates_and_verifies_in_fresh_read(tmp_path):
    receipt = execute_live_capability(FakeLiveCapability(), operation="live_verification", task="check live repo"); path = tmp_path / "receipt.json"; persist_live_operation_receipt(receipt, path); replayed = rehydrate_live_operation_receipt(path); assert replayed == receipt; assert replayed.verify()

def test_tampered_persisted_receipt_fails_closed(tmp_path):
    receipt = execute_live_capability(FakeLiveCapability(), operation="live_verification", task="check live repo"); path = tmp_path / "receipt.json"; persist_live_operation_receipt(receipt, path); payload = json.loads(path.read_text()); payload["target_resource"] = "other/repo"; path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="failed replay verification"): rehydrate_live_operation_receipt(path)

def test_swapped_persisted_receipt_fails_target_binding(tmp_path):
    receipt = execute_live_capability(FakeLiveCapability(target_resource="other/repo"), operation="live_verification", task="check live repo"); path = tmp_path / "receipt.json"; persist_live_operation_receipt(receipt, path); replayed = rehydrate_live_operation_receipt(path)
    with pytest.raises(ValueError, match="target does not match"): validate_report_claims(receipt=replayed, claim="Verified live repository state", expected_target_resource="dariusbrandon880-art/Sage", evidence_refs=(replayed.receipt_hash,))

def test_malformed_persisted_receipt_fails_closed(tmp_path):
    path = tmp_path / "receipt.json"; path.write_text("not-json")
    with pytest.raises(ValueError, match="unavailable or malformed"): rehydrate_live_operation_receipt(path)

def test_runtime_requires_connected_capability_for_live_directive():
    class FakeResponses:
        def create(self, **kwargs): return SimpleNamespace(output_text=structured_output())
    class FakeClient: responses = FakeResponses()
    with pytest.raises(ValueError, match="no connected live capability"): SAGERuntime(state()).invoke(OpenAIResponsesAdapter(FakeClient(), model_id="test"), "check live repo", model_role="c2")

def test_runtime_invokes_capability_before_model_and_binds_receipt():
    capability=FakeLiveCapability()
    class FakeResponses:
        def create(self, **kwargs): assert capability.calls == [("live_verification", "check live repo")]; return SimpleNamespace(output_text=structured_output())
    class FakeClient: responses = FakeResponses()
    response=SAGERuntime(state()).invoke(OpenAIResponsesAdapter(FakeClient(), model_id="test"), "check live repo", model_role="c2", live_capability=capability)
    assert response.live_operation_receipt is not None; assert response.live_operation_receipt.verify(); assert response.live_operation_receipt.receipt_hash in response.evidence_refs

def test_openai_system_instructions_embed_exact_order_and_recon_contract():
    instructions = _system_instructions(SAGERuntime(state()).envelope("c2")); assert CONTRACT_ID in instructions; assert "PRESERVE EXACTLY" in instructions; assert "INVOKE CONNECTED CAPABILITY" in instructions; assert "REPORT ONLY SUPPORTED FACTS" in instructions; assert RECON_POLICY_PATH in instructions; assert "DEEP RECON WITHOUT DRAG" in instructions

def test_station_spoof_is_rejected(): assert any("station identity mismatch" in v.lower() for v in SAGEProtocolGovernor.validate_and_parse(structured_output(station="[SAGE::FAKE::CHATGPT]")).violations)

def test_missing_station_is_rejected():
    missing=json.dumps({"reasoning_chain":["recon complete"],"proposed_actions":[],"epistemic_state":{"confidence_level":"LOW"},"evidence_refs":[]}); assert any("missing required sage station identity" in v.lower() for v in SAGEProtocolGovernor.validate_and_parse(missing).violations)

def test_openai_adapter_rejects_spoofed_station():
    class FakeResponses:
        def create(self, **kwargs): return SimpleNamespace(output_text=structured_output(station="[SAGE::FAKE::CHATGPT]"))
    class FakeClient: responses=FakeResponses()
    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"): SAGERuntime(state()).invoke(OpenAIResponsesAdapter(FakeClient(), model_id="test"), "recon", model_role="c2")

def test_validate_directive_compliance_verification():
    from sage.c2.chatgpt_c2_contract import validate_directive_compliance
    decision = validate_directive_compliance("verify live connection and run deep search go finish")
    assert decision.requires_live_verification is True
    assert decision.requires_deep_recon is True
    assert decision.requires_marathon_execution is True
    with pytest.raises(ValueError, match="empty"): validate_directive_compliance("")
