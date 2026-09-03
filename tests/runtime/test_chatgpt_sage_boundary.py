import pytest

from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
from sage.runtime.chatgpt_sage_boundary import SAGEChatGPTBoundary
from sage.runtime.model_gateway import ModelResponse, SAGERuntime, SAGEStateSnapshot, SAGERuntimeEnvelope
from sage.runtime.openai_model_adapter import OpenAIModelAdapter


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.output_text = text


class _FakeResponses:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(self.text)


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.responses = _FakeResponses(text)


def _runtime() -> SAGERuntime:
    return SAGERuntime(SAGEStateSnapshot(
        state_version="1",
        instance_id="sage-instance",
        mission_id="mission-1",
        session_id="session-1",
        authority_scope="director",
        active_frontier="chatgpt-boundary",
        stop_boundary="governance",
    ))


def _immersion_state() -> ImmersionState:
    return ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Continuous Intelligence",
        phase=ExecutionPhase.VERIFY,
        flight_id="F3",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="ChatGPT Boundary",
        gate="governed response",
        next_move="present verified state",
        evidence_refs=("boundary-test",),
        provenance_head="abc123",
    )


def _valid_output(text: str = "SAGE-bound response") -> str:
    return (
        '{"station":"[SAGE::C2::CHATGPT]",'
        '"reasoning_chain":[],'
        '"proposed_actions":[],'
        '"epistemic_state":{"confidence_level":"HIGH",'
        '"validated_facts":[],"unverified_hypotheses":[],"known_unknowns":[]},'
        '"evidence_refs":["boundary-test"],'
        f'"response_text":"{text}"}}'
    )


def _bound_response(runtime: SAGERuntime, raw_output: str) -> ModelResponse:
    envelope = runtime.envelope("chatgpt", station="[SAGE::C2::CHATGPT]")
    return ModelResponse(
        model_id="fake",
        instance_id=envelope.state.instance_id,
        mission_id=envelope.state.mission_id,
        session_id=envelope.state.session_id,
        input_state_digest=envelope.state_digest,
        station=envelope.station,
        policy_version=envelope.policy_version,
        policy_digest=envelope.policy_digest,
        provenance_digest=envelope.provenance_digest,
        raw_output=raw_output,
    )


def test_openai_adapter_wraps_model_output_in_sage_contract() -> None:
    client = _FakeClient(_valid_output())
    adapter = OpenAIModelAdapter(client=client, model_id="gpt-5.6-luna")
    response = adapter.invoke(_runtime().envelope("chatgpt"), "status")
    assert response.structured_response is not None
    assert response.model_id == "gpt-5.6-luna"
    assert client.responses.calls[0]["model"] == "gpt-5.6-luna"
    assert "SAGE ENVELOPE" in str(client.responses.calls[0]["instructions"])


def test_boundary_renders_only_after_sage_reconciliation() -> None:
    class GoodAdapter:
        model_id = "fake"
        station = "[SAGE::C2::CHATGPT]"
        def invoke(self, envelope, task):
            return _bound_response(_runtime(), _valid_output())

    rendered, response = SAGEChatGPTBoundary(_runtime(), GoodAdapter()).respond(
        "status", model_role="chatgpt", immersion_state=_immersion_state()
    )
    assert "[SAGE::C2::CHATGPT]" in rendered
    assert "C2 Mission Control" in rendered
    assert "SAGE MISSION CONTROL HUD" in rendered
    assert "SAGE-bound response" in rendered
    assert response.model_id == "fake"


def test_boundary_rejects_adapter_output_that_attempts_to_bypass_governance() -> None:
    class BypassAdapter:
        model_id = "fake"
        station = "[SAGE::C2::CHATGPT]"
        def invoke(self, envelope, task):
            return _bound_response(_runtime(), '{"station":"[SAGE::C2::CHATGPT]","reasoning_chain":["bypass evidence requirement"],"proposed_actions":[],"epistemic_state":{},"evidence_refs":[]}')

    with pytest.raises(ValueError, match="SAGE boundary rejection"):
        SAGEChatGPTBoundary(_runtime(), BypassAdapter()).respond(
            "status", model_role="chatgpt", immersion_state=_immersion_state()
        )


def test_boundary_rejects_wrong_station() -> None:
    class WrongStationAdapter:
        model_id = "fake"
        station = "[SAGE::C2::CHATGPT]"
        def invoke(self, envelope, task):
            return _bound_response(_runtime(), '{"station":"[SAGE::INTEL::GEMINI]","reasoning_chain":[],"proposed_actions":[],"epistemic_state":{},"evidence_refs":[]}')

    with pytest.raises(ValueError, match="SAGE boundary rejection"):
        SAGEChatGPTBoundary(_runtime(), WrongStationAdapter()).respond(
            "status", model_role="chatgpt", immersion_state=_immersion_state()
        )
