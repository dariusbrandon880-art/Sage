import json
from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS,
    CONTRACT_ID,
    CONTRACT_VERSION,
    classify_directive,
    render_system_contract,
    validate_report_claims,
)
from sage.c2.live_operation_receipt import LiveOperationReceipt, execute_live_capability
from sage.runtime.model_adapters import OpenAIResponsesAdapter, _system_instructions
from sage.runtime.model_gateway import SAGEProtocolGovernor, SAGERuntime, SAGEStateSnapshot


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="c2",
        stop_boundary="independent-verification",
    )


class FakeLiveCapability:
    capability_id = "github"

    def __init__(self, *, target_resource="dariusbrandon880-art/Sage"):
        self.calls = []
        self.target_resource = target_resource

    def invoke(self, *, operation: str, task: str):
        self.calls.append((operation, task))
        return {
            "target_resource": self.target_resource,
            "success": True,
            "result": {"head": "live-head", "operation": operation, "task": task},
        }


def structured_output(*, station="[SAGE::C2::CHATGPT]", claim="live repository verified"):
    return json.dumps({
        "station": station,
        "reasoning_chain": [claim],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "HIGH"},
        "evidence_refs": [],
    })


def test_contract_contains_all_ten_laws_and_identity():
    rendered = render_system_contract()
    assert CONTRACT_ID in rendered
    assert CONTRACT_VERSION in rendered
    assert len(ANTI_DRIFT_LAWS) == 10
    for law in ANTI_DRIFT_LAWS:
        assert law in rendered


def test_live_check_directive_requires_live_verification():
    decision = classify_directive("Check live repo and inspect PR")
    assert decision.requires_live_verification is True
    assert "check live repo" in decision.matched_triggers
    assert "inspect pr" in decision.matched_triggers


def test_normal_directive_does_not_force_live_check():
    decision = classify_directive("Design five future research frontiers")
    assert decision.requires_live_verification is False


def test_false_live_claim_fails_closed_without_receipt():
    with pytest.raises(ValueError, match="LiveOperationReceipt"):
        validate_report_claims(receipt=None, claim="Verified live repository state")


def test_boolean_cannot_substitute_for_receipt():
    with pytest.raises(ValueError, match="LiveOperationReceipt"):
        validate_report_claims(receipt=True, claim="Verified live repository state")  # type: ignore[arg-type]


def test_live_claim_requires_bound_receipt_evidence():
    capability = FakeLiveCapability()
    receipt = execute_live_capability(capability, operation="live_verification", task="check live repo")
    with pytest.raises(ValueError, match="not bound to response evidence"):
        validate_report_claims(
            receipt=receipt,
            claim="Verified live repository state",
            expected_target_resource=receipt.target_resource,
            evidence_refs=(),
        )


def test_live_claim_accepts_authentic_bound_receipt():
    capability = FakeLiveCapability()
    receipt = execute_live_capability(capability, operation="live_verification", task="check live repo")
    validate_report_claims(
        receipt=receipt,
        claim="Verified live repository state",
        expected_target_resource=receipt.target_resource,
        evidence_refs=(receipt.receipt_hash,),
    )


def test_receipt_is_created_only_after_capability_invocation():
    capability = FakeLiveCapability()
    receipt = execute_live_capability(capability, operation="live_verification", task="check live repo")
    assert capability.calls == [("live_verification", "check live repo")]
    assert isinstance(receipt, LiveOperationReceipt)
    assert receipt.verify()
    assert receipt.success is True


def test_runtime_requires_connected_capability_for_live_directive():
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text=structured_output())

    class FakeClient:
        responses = FakeResponses()

    runtime = SAGERuntime(state())
    adapter = OpenAIResponsesAdapter(FakeClient(), model_id="test")
    with pytest.raises(ValueError, match="no connected live capability"):
        runtime.invoke(adapter, "check live repo", model_role="c2")


def test_runtime_invokes_capability_before_model_and_binds_receipt():
    call_order = []
    capability = FakeLiveCapability()

    class FakeResponses:
        def create(self, **kwargs):
            call_order.append("model")
            assert capability.calls == [("live_verification", "check live repo")]
            return SimpleNamespace(output_text=structured_output())

    class FakeClient:
        responses = FakeResponses()

    runtime = SAGERuntime(state())
    response = runtime.invoke(
        OpenAIResponsesAdapter(FakeClient(), model_id="test"),
        "check live repo",
        model_role="c2",
        live_capability=capability,
    )
    call_order.append("complete")
    assert call_order == ["model", "complete"]
    assert response.live_operation_receipt is not None
    assert response.live_operation_receipt.verify()
    assert response.live_operation_receipt.receipt_hash in response.evidence_refs


def test_runtime_rejects_live_claim_with_wrong_resource():
    capability = FakeLiveCapability(target_resource="wrong/repo")

    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text=structured_output())

    class FakeClient:
        responses = FakeResponses()

    runtime = SAGERuntime(state())
    response = runtime.invoke(
        OpenAIResponsesAdapter(FakeClient(), model_id="test"),
        "check live repo",
        model_role="c2",
        live_capability=capability,
    )
    assert response.live_operation_receipt.target_resource == "wrong/repo"


def test_openai_system_instructions_embed_exact_order_contract():
    envelope = SAGERuntime(state()).envelope("c2")
    instructions = _system_instructions(envelope)
    assert CONTRACT_ID in instructions
    assert "PRESERVE EXACTLY" in instructions
    assert "INVOKE CONNECTED CAPABILITY" in instructions
    assert "REPORT ONLY SUPPORTED FACTS" in instructions


def test_station_spoof_is_rejected():
    spoofed = structured_output(station="[SAGE::FAKE::CHATGPT]")
    structured = SAGEProtocolGovernor.validate_and_parse(spoofed)
    assert any("station identity mismatch" in violation.lower() for violation in structured.violations)


def test_missing_station_is_rejected():
    missing = json.dumps({
        "reasoning_chain": ["recon complete"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "LOW"},
        "evidence_refs": [],
    })
    structured = SAGEProtocolGovernor.validate_and_parse(missing)
    assert any("missing required sage station identity" in violation.lower() for violation in structured.violations)


def test_openai_adapter_rejects_spoofed_station():
    spoofed = structured_output(station="[SAGE::FAKE::CHATGPT]")

    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text=spoofed)

    class FakeClient:
        responses = FakeResponses()

    runtime = SAGERuntime(state())
    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        runtime.invoke(OpenAIResponsesAdapter(FakeClient(), model_id="test"), "recon", model_role="c2")
