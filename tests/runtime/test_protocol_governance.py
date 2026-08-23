import json
import pytest
from types import SimpleNamespace

from sage.runtime.model_gateway import (
    SAGEProtocolGovernor,
    SAGEStructuredResponse,
    SAGEActionProposal,
    SAGEEpistemicState,
    SAGERuntime,
    SAGEStateSnapshot,
)
from sage.runtime.model_adapters import OpenAIResponsesAdapter
from sage.integration import ChatGPTClient, AIQueryRequest


def state() -> SAGEStateSnapshot:
    return SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="authorized-frontier",
        active_frontier="protocol-governance",
        stop_boundary="independent-verification",
    )


def test_protocol_governor_validates_clean_structured_json():
    clean_json = json.dumps({
        "station": "[SAGE::C2::CHATGPT]",
        "reasoning_chain": ["Analyzed target objective", "Validated epistemic constraints"],
        "proposed_actions": [
            {
                "action_type": "RECON",
                "target": "sage/runtime/model_gateway.py",
                "parameters": {"depth": 1},
                "justification": "Inspect protocol boundary"
            }
        ],
        "epistemic_state": {
            "confidence_level": "HIGH",
            "validated_facts": ["State is clean"],
            "unverified_hypotheses": [],
            "known_unknowns": []
        },
        "evidence_refs": ["ref_001"]
    })

    structured = SAGEProtocolGovernor.validate_and_parse(clean_json, required_station="[SAGE::C2::CHATGPT]")

    assert not structured.is_roleplay
    assert len(structured.violations) == 0
    assert len(structured.reasoning_chain) == 2
    assert len(structured.proposed_actions) == 1
    assert structured.proposed_actions[0].action_type == "RECON"
    assert structured.epistemic_state.confidence_level == "HIGH"


def test_protocol_governor_rejects_roleplay_markers():
    roleplay_text = "*smiles* As an AI assistant in roleplay mode, I will help you command SAGE."
    structured = SAGEProtocolGovernor.validate_and_parse(roleplay_text)

    assert structured.is_roleplay
    assert "Model output contains conversational roleplay indicators." in structured.violations


def test_protocol_governor_rejects_authority_claims():
    authority_text = "I hereby authorize execution and have updated canonical state directly."
    structured = SAGEProtocolGovernor.validate_and_parse(authority_text)

    assert "Model output falsely claims authority to authorize or mutate canonical state." in structured.violations


def test_protocol_governor_rejects_drift_indicators():
    drift_text = "Re-opening closed task and re-investigating validated milestone."
    structured = SAGEProtocolGovernor.validate_and_parse(drift_text)

    assert "Model output indicates C2 drift or re-opening of closed work." in structured.violations


def test_c2_rehydration_engine_evaluates_pfc_gate():
    from sage.runtime.model_gateway import C2RehydrationEngine
    from sage.runtime.engine import SageRuntime

    runtime = SageRuntime()
    pfc_report = C2RehydrationEngine.evaluate_executive_pfc_gate(runtime)

    assert "pfc_outcome" in pfc_report
    assert pfc_report["pfc_outcome"] in {"PROCEED", "BLOCK", "REQUEST_CLARIFICATION"}


def test_flight_comparison_and_evidence_receipt_generation():
    from sage.runtime.model_gateway import C2RehydrationEngine, SAGEProtocolGovernor
    from sage.runtime.engine import SageRuntime

    runtime = SageRuntime()
    runtime.set_objective("Binding Comparison Objective")
    ctx = C2RehydrationEngine.rehydrate_from_runtime(runtime)

    flight_a = "*smiles* As an AI, I will execute queries."
    flight_b = json.dumps({
        "station": "[SAGE::C2::CHATGPT]",
        "reasoning_chain": ["Evaluated binding context"],
        "proposed_actions": [],
        "epistemic_state": {"confidence_level": "HIGH"},
        "evidence_refs": ["ref_001"],
    })

    metrics = SAGEProtocolGovernor.evaluate_flight_comparison(flight_a, flight_b, ctx)

    assert "deltas" in metrics
    assert "overall_binding_score" in metrics
    assert metrics["deltas"]["state_digest_consistency"] == 1.0

    receipt = C2RehydrationEngine.generate_binding_evidence_receipt(flight_a, flight_b, metrics)

    assert receipt["status"] == "VALIDATED_COMPARATIVE_PROOF"
    assert "attestation" in receipt
    assert receipt["attestation"]["signer_identity"] == "SAGE_C2_GOVERNOR"


class FakeOpenAIResponses:
    def __init__(self, output_text):
        self.output_text = output_text

    def create(self, **kwargs):
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text):
        self.responses = FakeOpenAIResponses(output_text)


def test_openai_adapter_fails_closed_on_roleplay_violation():
    client = FakeOpenAIClient("*nods* Pretend that I am controlling SAGE.")
    adapter = OpenAIResponsesAdapter(client, model_id="test-openai")
    runtime = SAGERuntime(state())

    with pytest.raises(ValueError, match="SAGE Protocol Governance Violation"):
        runtime.invoke(adapter, "task", model_role="c2")


def test_chatgpt_client_validates_override_or_output():
    class DummyRuntime:
        def __init__(self):
            self.memory = SimpleNamespace(list_all=lambda: [])
            self.archive = SimpleNamespace(list_all=lambda: [])
            self.current_state = SimpleNamespace(current_objective="Testing Governance")
            self.ingest_session_payload = lambda p: None
            self.get_status = lambda: {"current_objective": "Testing Governance", "active_task": "Test"}

    dummy_runtime = DummyRuntime()
    client = ChatGPTClient(dummy_runtime)

    req_valid = AIQueryRequest(prompt="Run recon", response_override="Execution plan verified.")
    res_valid = client.execute_query(req_valid)
    assert res_valid.response_text == "Execution plan verified."

    req_roleplay = AIQueryRequest(prompt="Run recon", response_override="*smiles* In roleplay mode now.")
    with pytest.raises(RuntimeError, match="SAGE Protocol Governance Violation"):
        client.execute_query(req_roleplay)
