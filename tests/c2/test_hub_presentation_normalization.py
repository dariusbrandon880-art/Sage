import pytest

from sage.c2.hub_presentation_boundary import (
    HubSurface,
    normalize_hub_presentation,
    recognize_hub,
)
from sage.c2.immersion_rehydration import is_rehydrate_hud_command


HUB = """🛰️ SAGE C2 HUD & Organism Agent Projection // LIVE
01 — COMMAND BAND
[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL
02 — OPERATING PICTURE
03 — PROGRESSION / IMPACT
04 — STRIKE FEED // HIGH-TEMPO EVENTS
05 — ORGANISM PROGRESSION
SAGE ORGANISM // AGENT PROJECTION
"""

HUB_A = """01 — COMMAND BAND
02 — OPERATING PICTURE
03 — PROGRESSION / IMPACT
04 — STRIKE FEED
"""

HUB_B = """05 — ORGANISM PROGRESSION
SAGE ORGANISM // AGENT PROJECTION
"""


@pytest.mark.parametrize(
    "transport",
    [
        HUB,
        f"```text\n{HUB}\n```",
        f"Jules execution report:\n```\n{HUB}\n```",
        f"### archived context\n{HUB}",
    ],
)
def test_recognition_discards_transport_framing(transport):
    obj = recognize_hub(transport)
    assert obj is not None
    assert obj.surface is HubSurface.COMPOSITE
    assert obj.has_hub_a is True
    assert obj.has_hub_b is True


def test_hub_a_and_hub_b_are_semantically_distinct():
    assert recognize_hub(HUB_A).surface is HubSurface.HUB_A
    assert recognize_hub(HUB_B).surface is HubSurface.HUB_B


def test_partial_layer_text_is_not_promoted_to_hub():
    assert recognize_hub("01 — COMMAND BAND\nordinary prose") is None


def test_non_hub_transport_is_untouched():
    assert normalize_hub_presentation("ordinary SAGE task", manager=object()) is None


def test_normalization_delegates_to_canonical_renderer(monkeypatch):
    from sage.experimental.airspace import immersion

    calls = []

    def fake_renderer(manager, *, status="READY"):
        calls.append((manager, status))
        return "CANONICAL_RENDERER_OUTPUT"

    monkeypatch.setattr(immersion, "render_four_layer_hud_from_manager", fake_renderer)
    manager = object()

    rendered = normalize_hub_presentation(f"```\n{HUB}\n```", manager, status="LOCKED")

    assert rendered == "CANONICAL_RENDERER_OUTPUT"
    assert calls == [(manager, "LOCKED")]


def test_normalization_never_echoes_transport_representation(monkeypatch):
    from sage.experimental.airspace import immersion

    monkeypatch.setattr(
        immersion,
        "render_four_layer_hud_from_manager",
        lambda manager, *, status="READY": "01 — COMMAND BAND\n02 — OPERATING PICTURE\n03 — PROGRESSION / IMPACT\n04 — STRIKE FEED\n05 — ORGANISM PROGRESSION",
    )

    rendered = normalize_hub_presentation(f"```markdown\n{HUB}\n```", object())
    assert "```markdown" not in rendered
    assert "SAGE C2 HUD & Organism Agent Projection // LIVE" not in rendered
    assert "01 — COMMAND BAND" in rendered
    assert "05 — ORGANISM PROGRESSION" in rendered


def test_missing_manager_fails_closed_after_recognition():
    with pytest.raises(ValueError, match="Airspace manager"):
        normalize_hub_presentation(HUB, None)


def test_pasted_hub_is_an_immersion_trigger_not_transport_instruction():
    assert is_rehydrate_hud_command(f"```text\n{HUB}\n```") is True
    assert is_rehydrate_hud_command(HUB) is True
    assert is_rehydrate_hud_command("ordinary SAGE task") is False
