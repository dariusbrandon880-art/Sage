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
