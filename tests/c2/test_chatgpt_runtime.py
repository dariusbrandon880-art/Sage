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


def test_runtime_preserves_direct_organism_tag_and_projection_inputs() -> None:
    tag = "[SAGE::C2::CHATGPT] ◈ GPT // CQL-1 // SQL-0 // POINTS 50 // XP 5 // BOSS ⭐×0 ⭐⭐×0 // ⚔️ 0 // ┃ 0 // READY"
    projection = object()

    response = build_chatgpt_c2_response(
        _state(),
        "Turn message",
        organism_projection=projection,
        organism_tag=tag,
    )

    assert response.organism_projection is projection
    assert response.organism_tag == tag
    assert tag in response.render()


def test_runtime_manager_alias_is_forwarded(tmp_path) -> None:
    from sage.experimental.airspace.manager import AirspaceManager

    rendered = render_chatgpt_c2_response(
        _state(),
        "Manager alias",
        manager=AirspaceManager(tmp_path / "ledger.json"),
    )

    assert "POINTS 0" in rendered
    assert "Manager alias" in rendered
