from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS,
    CONTRACT_VERSION,
    HUB_PRESENTATION_BOUNDARY_PATH,
    render_system_contract,
)


def test_c2_contract_locks_jules_report_vs_two_hub_distinction():
    assert CONTRACT_VERSION == "1.8"
    assert HUB_PRESENTATION_BOUNDARY_PATH == "docs/governance/SAGE_C2_HUB_PRESENTATION_BOUNDARY.md"
    assert any("Jules reports are execution intelligence/claims" in law for law in ANTI_DRIFT_LAWS)
    assert any("Hub A" in law and "Hub B" in law for law in ANTI_DRIFT_LAWS)


def test_c2_system_contract_exposes_hub_presentation_rule():
    contract = render_system_contract()
    assert "HUB PRESENTATION BOUNDARY:" in contract
    assert "HUB PRESENTATION RULE:" in contract
    assert "Hub A is the C2 Mission Control HUD/Four-Layer Operating Board" in contract
    assert "Hub B is the SAGE Organism/Agent Projection" in contract
    assert "do not replace it with ordinary prose" in contract


def test_canonical_immersion_surface_preserves_four_layers_plus_organism_projection():
    from sage.experimental.airspace.immersion import render_four_layer_hud
    from sage.experimental.airspace.renderer import AirspaceRenderer

    assert callable(render_four_layer_hud)
    assert callable(AirspaceRenderer.render_c2_board_from_manager)


def test_chatgpt_immersion_hub_cannot_be_suppressed_by_continuity_key():
    from sage.c2.chatgpt_immersion import project_chatgpt_immersion_response
    from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus

    state = ImmersionState(
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
    tag = "[SAGE::C2::CHATGPT] ◈ GPT // CQL-? // SQL-? // POINTS ? // XP ? // BOSS ⭐×? ⭐⭐×? // ⚔️ ? // ┃ ? // READY"

    response = project_chatgpt_immersion_response(
        state,
        organism_tag=tag,
        hud_visible=False,
        previous_hud_update_key="same-key",
        force_hud=False,
    )

    assert response.should_render_hud is True


def test_hub_presentation_boundary_recognition_and_normalization(tmp_path):
    from sage.c2.hub_presentation_boundary import (
        HubSurface,
        normalize_hub_presentation,
        recognize_hub,
        render_canonical_hub,
    )
    from sage.experimental.airspace.manager import AirspaceManager

    hub_a = (
        "01 — COMMAND BAND\n"
        "02 — OPERATING PICTURE\n"
        "03 — PROGRESSION / IMPACT\n"
        "04 — STRIKE FEED\n"
    )
    hub_b = "05 — ORGANISM PROGRESSION"
    composite = f"{hub_a}\n{hub_b}"

    rec_a = recognize_hub(hub_a)
    assert rec_a is not None
    assert rec_a.surface == HubSurface.HUB_A
    assert rec_a.has_hub_a is True
    assert rec_a.has_hub_b is False

    rec_b = recognize_hub(hub_b)
    assert rec_b is not None
    assert rec_b.surface == HubSurface.HUB_B
    assert rec_b.has_hub_a is False
    assert rec_b.has_hub_b is True

    rec_comp = recognize_hub(composite)
    assert rec_comp is not None
    assert rec_comp.surface == HubSurface.COMPOSITE
    assert rec_comp.is_hub is True

    assert recognize_hub("just plain text without layers") is None
    assert recognize_hub("") is None

    mgr = AirspaceManager(tmp_path / "ledger.json")
    rendered = render_canonical_hub(mgr)
    assert "01 — COMMAND BAND" in rendered
    assert "05 — ORGANISM PROGRESSION" in rendered

    normalized = normalize_hub_presentation(hub_a, mgr)
    assert normalized is not None
    assert "01 — COMMAND BAND" in normalized
    assert normalize_hub_presentation("random text", mgr) is None


def test_chatgpt_immersion_defaults_to_persistent_hub_reconstruction():
    import inspect
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse, project_chatgpt_immersion_response

    response_default = inspect.signature(ChatGPTImmersionResponse).parameters["force_hud"].default
    projection_default = inspect.signature(project_chatgpt_immersion_response).parameters["force_hud"].default

    assert response_default is True
    assert projection_default is True
