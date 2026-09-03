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


def test_chatgpt_immersion_renders_organism_tag(tmp_path) -> None:
    from sage.experimental.airspace.manager import AirspaceManager
    from sage.experimental.airspace.models import StationID
    from sage.experimental.airspace.organism_projection import OrganismProjection

    state = _state()

    # 1. Direct organism tag string
    tag_str = "SAGE C2 Mission Control // CQL-1 // POINTS 100 // XP 10 // BOSS ⭐×1 ⭐⭐×0 // ⚔️ 1 // ┃ 0 // READY"
    res1 = project_chatgpt_immersion_response(state, body="Tag test", organism_tag=tag_str)
    rendered1 = res1.render()
    assert tag_str in rendered1

    # 2. Manager-backed organism projection
    manager = AirspaceManager(tmp_path / "ledger.json")
    res2 = project_chatgpt_immersion_response(state, body="Manager tag test", manager=manager)
    rendered2 = res2.render()
    assert "POINTS 0" in rendered2
    assert "XP 0" in rendered2
    assert "BOSS ⭐×0 ⭐⭐×0" in rendered2
    assert "⚔️ 0 // ┃ 0" in rendered2

    # 3. Direct OrganismAgentProjection instance with organism_tag=None
    airspace_state = manager.reconstruct_airspace_state()
    proj = OrganismProjection.project_station(manager, airspace_state, StationID.MISSION_CONTROL)
    res3 = project_chatgpt_immersion_response(state, body="Direct projection test", organism_projection=proj)
    # Ensure organism_tag is rendered via fallback in render() when organism_tag=None
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse
    res3_direct = ChatGPTImmersionResponse(
        station_header="[SAGE::C2::CHATGPT] **C2 Mission Control**",
        immersion_envelope=res3.immersion_envelope,
        body="Direct instance test",
        organism_projection=proj,
        organism_tag=None,
    )
    rendered3 = res3_direct.render()
    assert "POINTS 0" in rendered3
    assert "XP 0" in rendered3
