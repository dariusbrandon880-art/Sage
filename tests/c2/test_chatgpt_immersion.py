from sage.c2.chatgpt_immersion import project_chatgpt_immersion_response
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


def test_chatgpt_immersion_projects_canonical_state_without_mutation() -> None:
    state = _state()
    rendered = project_chatgpt_immersion_response(state, "Mission update").render()

    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert "MISSION CONTROL" in rendered
    assert "SAGE MISSION CONTROL HUD" in rendered
    assert "MISSION  : Governed Continuous Intelligence" in rendered
    assert "FLIGHT   : F3 (ACTIVE)" in rendered
    assert "EVIDENCE : 1 verified ref(s) [wave-a]" in rendered
    assert "Mission update" in rendered
    assert state.to_dict()["trust_status"] == "VERIFIED"


def test_chatgpt_immersion_is_read_only() -> None:
    state = _state()
    response = project_chatgpt_immersion_response(state)

    assert response.immersion_envelope.read_only is True
    assert response.immersion_envelope.authority == "canonical_immersion_state"


def test_chatgpt_immersion_renders_strike_feed() -> None:
    from sage.c2.immersion_projection import StrikeEvent, StrikeFeedProjection

    state = _state()
    custom_feed = StrikeFeedProjection(
        events=(
            StrikeEvent("TARGET ACQUIRED", "🎯", "Custom Frontier", "Gate: Test"),
            StrikeEvent("TARGET KILLED", "◆", "Seam Closed", "Custom"),
        )
    )

    response = project_chatgpt_immersion_response(
        state,
        body="Custom strike feed turn",
        strike_feed=custom_feed,
    )

    rendered = response.render()
    assert "04 — STRIKE FEED" in rendered
    assert "🎯 TARGET ACQUIRED // Custom Frontier" in rendered
    assert "◆ TARGET KILLED // Seam Closed" in rendered
    assert "Custom strike feed turn" in rendered
