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
