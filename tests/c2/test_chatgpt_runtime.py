from sage.c2.chatgpt_runtime import build_chatgpt_c2_response, render_chatgpt_c2_response
from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


def _state() -> ImmersionState:
    return ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Continuous Intelligence",
        phase=ExecutionPhase.VERIFY,
        flight_id="F3",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="Core Immersion",
        gate="projection contract",
        next_move="present verified state",
        evidence_refs=("wave-a",),
        provenance_head="abc123",
    )


def test_runtime_renders_through_chatgpt_immersion_surface() -> None:
    rendered = render_chatgpt_c2_response(_state(), "Mission update")

    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert "C2 Mission Control" in rendered
    assert "SAGE MISSION CONTROL HUD" in rendered
    assert "MISSION  : Governed Continuous Intelligence" in rendered
    assert "FLIGHT   : F3 (ACTIVE)" in rendered
    assert "EVIDENCE : 1 verified ref(s) [wave-a]" in rendered
    assert "Mission update" in rendered


def test_runtime_exposes_structured_read_only_response() -> None:
    response = build_chatgpt_c2_response(_state())

    assert response.immersion_envelope.read_only is True
    assert response.immersion_envelope.authority == "canonical_immersion_state"
    assert response.station_header == "[SAGE::C2::CHATGPT] **C2 Mission Control**"
