from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse, project_chatgpt_immersion_response
from sage.c2.immersion_projection import project_c2_response_contract
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


def test_chatgpt_organism_hud_is_first_layer_when_present() -> None:
    state = _state()
    contract = project_c2_response_contract(state)
    response = ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=contract,
        body="Mission body",
        organism_tag=(
            "[SAGE::C2::CHATGPT] ◈ GPT // CQL-? // SQL-? // POINTS ? // XP ? // "
            "BOSS ⭐×? ⭐⭐×? // ⚔️ ? // ┃ ? // READY"
        ),
    )

    rendered = response.render()
    hud_index = rendered.index("POINTS ?")
    mission_index = rendered.index("C2 Mission Control")
    body_index = rendered.index("Mission body")

    assert hud_index < mission_index < body_index
    assert rendered.startswith("[SAGE::C2::CHATGPT] ◈ GPT // CQL-?")


def test_chatgpt_organism_tag_rendered_by_default() -> None:
    state = _state()
    response = project_chatgpt_immersion_response(state, "Turn body")
    assert response.organism_tag is not None
    assert "POINTS" in response.organism_tag
    assert "BOSS" in response.organism_tag

    rendered = response.render()
    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert "POINTS" in rendered
    assert "C2 Mission Control" in rendered
