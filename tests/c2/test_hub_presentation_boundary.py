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
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse

    response = ChatGPTImmersionResponse.__new__(ChatGPTImmersionResponse)
    response.hud_visible = False
    response.previous_hud_update_key = "same-key"
    response.force_hud = False

    assert response.should_render_hud is True


def test_chatgpt_immersion_defaults_to_persistent_hub_reconstruction():
    import inspect
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse, project_chatgpt_immersion_response

    response_default = inspect.signature(ChatGPTImmersionResponse).parameters["force_hud"].default
    projection_default = inspect.signature(project_chatgpt_immersion_response).parameters["force_hud"].default

    assert response_default is True
    assert projection_default is True
