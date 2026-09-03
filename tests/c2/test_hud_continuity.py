from types import SimpleNamespace

import pytest

from sage.c2.chatgpt_immersion import project_chatgpt_immersion_response
from sage.c2.immersion_projection import (
    ExecutionPhase,
    FlightStatus,
    ImmersionState,
    TrustStatus,
)
from sage.c2.response_envelope import hud_update_key, should_render_hud


def _state(next_move: str = "present verified state") -> ImmersionState:
    return ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Continuous Intelligence",
        phase=ExecutionPhase.VERIFY,
        flight_id="F3",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="Core Immersion",
        gate="projection contract",
        next_move=next_move,
        evidence_refs=("wave-a",),
        provenance_head="abc123",
    )


def _tag() -> str:
    return "[SAGE::C2::CHATGPT] ◈ GPT // CQL-? // SQL-? // POINTS ? // XP ? // BOSS ⭐×? ⭐⭐×? // ⚔️ ? // ┃ ? // READY"


def test_hud_update_key_changes_when_visible_hud_changes() -> None:
    first = project_chatgpt_immersion_response(_state(), organism_tag=_tag())
    second = project_chatgpt_immersion_response(
        _state("verify updated evidence"), organism_tag=_tag()
    )

    assert first.hud_update_key != second.hud_update_key
    assert first.should_render_hud is True
    assert second.should_render_hud is True


def test_unchanged_hud_can_be_suppressed_after_first_render() -> None:
    response = project_chatgpt_immersion_response(_state(), organism_tag=_tag())
    repeated = project_chatgpt_immersion_response(
        _state(),
        organism_tag=_tag(),
        previous_hud_update_key=response.hud_update_key,
    )

    assert response.should_render_hud is True
    assert repeated.should_render_hud is False
    assert "SAGE MISSION CONTROL HUD" not in repeated.render()
    assert "C2 Mission Control" in repeated.render()
    assert "◈ GPT" in repeated.render()


def test_force_hud_reopens_unchanged_hud() -> None:
    response = project_chatgpt_immersion_response(_state(), organism_tag=_tag())
    repeated = project_chatgpt_immersion_response(
        _state(),
        organism_tag=_tag(),
        previous_hud_update_key=response.hud_update_key,
        force_hud=True,
    )
    assert repeated.should_render_hud is True
    assert "SAGE MISSION CONTROL HUD" in repeated.render()


def test_hud_can_be_hidden_explicitly_without_dropping_name_tag() -> None:
    response = project_chatgpt_immersion_response(
        _state(), organism_tag=_tag(), hud_visible=False
    )
    rendered = response.render()
    assert "SAGE MISSION CONTROL HUD" not in rendered
    assert "◈ GPT" in rendered
    assert "C2 Mission Control" in rendered


def test_hud_continuity_rejects_empty_key() -> None:
    with pytest.raises(ValueError, match="non-empty current key"):
        should_render_hud("")


def test_hud_update_key_requires_renderable_hud() -> None:
    with pytest.raises(ValueError, match="renderable HUD"):
        hud_update_key(SimpleNamespace())


def test_explicit_bad_organism_projection_fails_closed_instead_of_dropping_tag() -> None:
    broken = SimpleNamespace(render_agent_tag=lambda: "")
    with pytest.raises(ValueError, match="name tag"):
        project_chatgpt_immersion_response(
            _state(), organism_projection=broken
        )
