from sage.c2.chatgpt_c2_contract import (
    ANTI_DRIFT_LAWS,
    CONTRACT_VERSION,
    HUB_PRESENTATION_BOUNDARY_PATH,
    render_system_contract,
)


def test_c2_contract_locks_jules_report_vs_two_hub_distinction():
    assert CONTRACT_VERSION == "1.9"
    assert HUB_PRESENTATION_BOUNDARY_PATH == "docs/governance/SAGE_C2_HUB_PRESENTATION_BOUNDARY.md"
    assert any("Jules reports are execution intelligence/claims" in law for law in ANTI_DRIFT_LAWS)
    assert any("Hub A" in law and "Hub B" in law for law in ANTI_DRIFT_LAWS)
    assert any("not a third HUD" in law for law in ANTI_DRIFT_LAWS)
    assert any("requirement to repeat both surfaces" in law for law in ANTI_DRIFT_LAWS)


def test_c2_system_contract_exposes_hub_presentation_rule():
    contract = render_system_contract()
    assert "HUB PRESENTATION BOUNDARY:" in contract
    assert "HUB PRESENTATION RULE:" in contract
    assert "Hub A is the C2 Mission Control HUD/Four-Layer Operating Board" in contract
    assert "Hub B is the SAGE Organism/Agent Projection" in contract
    assert "must not repeat both merely because both exist" in contract


def test_canonical_immersion_surface_exposes_separate_hub_renderers():
    from sage.experimental.airspace.immersion import (
        render_four_layer_hud,
        render_four_layer_hud_from_manager,
        render_hub_a_from_manager,
        render_hub_b_from_manager,
    )
    from sage.experimental.airspace.renderer import AirspaceRenderer

    assert callable(render_four_layer_hud)
    assert callable(render_four_layer_hud_from_manager)
    assert callable(render_hub_a_from_manager)
    assert callable(render_hub_b_from_manager)
    assert callable(AirspaceRenderer.render_c2_board_from_manager)


def test_hub_boundary_recognizes_contextual_surfaces_without_collapsing_them():
    from sage.c2.hub_presentation_boundary import HubSurface, recognize_hub

    hub_a = "\n".join(
        (
            "01 — COMMAND BAND",
            "02 — OPERATING PICTURE",
            "03 — PROGRESSION / IMPACT",
            "04 — STRIKE FEED",
        )
    )
    hub_b = "SAGE ORGANISM // AGENT PROJECTION\nJules // RANK Lvl 4"
    composite = f"{hub_a}\n{hub_b}"

    assert recognize_hub(hub_a).surface is HubSurface.HUB_A
    assert recognize_hub(hub_b).surface is HubSurface.HUB_B
    assert recognize_hub(composite).surface is HubSurface.COMPOSITE


def test_hub_boundary_defaults_to_hub_a_and_allows_explicit_composite():
    import inspect
    from sage.c2.hub_presentation_boundary import HubSurface, render_canonical_hub

    signature = inspect.signature(render_canonical_hub)
    assert signature.parameters["surface"].default is HubSurface.HUB_A


def test_chatgpt_immersion_hub_cannot_be_suppressed_by_continuity_key():
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse

    response = ChatGPTImmersionResponse.__new__(ChatGPTImmersionResponse)
    object.__setattr__(response, "hud_visible", False)
    object.__setattr__(response, "previous_hud_update_key", "same-key")
    object.__setattr__(response, "force_hud", True)

    assert response.should_render_hud is True


def test_chatgpt_immersion_defaults_to_persistent_hub_reconstruction():
    import inspect
    from sage.c2.chatgpt_immersion import ChatGPTImmersionResponse, project_chatgpt_immersion_response

    response_default = inspect.signature(ChatGPTImmersionResponse).parameters["force_hud"].default
    projection_default = inspect.signature(project_chatgpt_immersion_response).parameters["force_hud"].default

    assert response_default is False
    assert projection_default is False
