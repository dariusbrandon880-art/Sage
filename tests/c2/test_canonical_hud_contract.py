from pathlib import Path


SPEC = Path(__file__).parents[2] / "docs" / "governance" / "SAGE_HUD_CANONICAL_SPEC.md"


def test_canonical_hud_contract_exists_and_is_versioned():
    text = SPEC.read_text(encoding="utf-8")
    assert "Contract ID:** `SAGE-HUD-CANONICAL`" in text
    assert "Schema Version:** `1.0`" in text


def test_canonical_hud_sections_and_order_are_locked():
    text = SPEC.read_text(encoding="utf-8")
    identifiers = (
        "01 — COMMAND BAND",
        "02 — OPERATING PICTURE",
        "03 — PROGRESSION / IMPACT",
        "04 — STRIKE FEED // HIGH-TEMPO EVENTS",
        "05 — ORGANISM PROGRESSION",
        "SAGE ORGANISM // AGENT PROJECTION",
    )
    positions = [text.index(identifier) for identifier in identifiers]
    assert positions == sorted(positions)
    for identifier in identifiers:
        assert text.count(identifier) >= 1


def test_canonical_hud_contract_locks_identity_and_fail_closed_rules():
    text = SPEC.read_text(encoding="utf-8")
    for marker in (
        "[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL",
        "NO REDESIGN",
        "NO SUBSTITUTION",
        "NO FABRICATION",
        "NO THIRD HUD",
        "REHYDRATION FAILURE",
        "NO REPORT FALLBACK",
        "HUB_A",
        "HUB_B",
        "COMPOSITE",
    ):
        assert marker in text


def test_canonical_hud_contract_binds_state_semantics():
    text = SPEC.read_text(encoding="utf-8")
    for field in (
        "STATUS",
        "QUAL",
        "MISSION",
        "ACTIVE SORTIES",
        "TOTAL SYSTEM XP",
        "agent_name",
        "RANK",
        "POINTS",
        "XP",
        "BOSS",
    ):
        assert field in text


def test_existing_runtime_remains_the_renderer_authority():
    from sage.c2.hub_presentation_boundary import HubSurface, render_canonical_hub
    from sage.experimental.airspace.immersion import (
        render_hub_a_from_manager,
        render_hub_b_from_manager,
        render_four_layer_hud_from_manager,
    )

    assert HubSurface.HUB_A.value == "HUB_A"
    assert HubSurface.HUB_B.value == "HUB_B"
    assert HubSurface.COMPOSITE.value == "COMPOSITE"
    assert callable(render_canonical_hub)
    assert callable(render_hub_a_from_manager)
    assert callable(render_hub_b_from_manager)
    assert callable(render_four_layer_hud_from_manager)
