"""Unit tests for ChatGPT immersion rehydration and full C2 frame rehydration."""

from types import SimpleNamespace
import pytest

from sage.c2.immersion_rehydration import (
    C2_OPERATING_FRAME_SEQUENCE,
    build_chatgpt_immersion_state,
    rehydrate_chatgpt_c2_frame,
)


def _mock_runtime() -> SimpleNamespace:
    return SimpleNamespace(
        current_state=SimpleNamespace(
            current_objective="Reconcile organism feedback loop",
            active_task="Execute full game immersion rehydration",
            blockers=[],
            dependencies=[],
        ),
        get_status=lambda: {"c2_status": {"rehydrated": True}},
    )


def test_build_chatgpt_immersion_state_rehydrates_operating_frame():
    runtime = _mock_runtime()
    state = build_chatgpt_immersion_state(runtime, session_id="test_session_001")

    assert state.station_identity == "[SAGE::C2::CHATGPT]"
    assert state.mission == "Reconcile organism feedback loop"
    assert state.next_move == "Execute full game immersion rehydration"
    assert state.provenance_head is not None
    assert len(state.provenance_head) == 64


def test_rehydrate_chatgpt_c2_frame_builds_full_immersion_response():
    runtime = _mock_runtime()
    immersion_state, response = rehydrate_chatgpt_c2_frame(
        runtime,
        session_id="test_session_002",
        body="C2 operating frame locked onto live repo truth.",
    )

    assert immersion_state.flight_id == "C2:test_session_002"
    assert response.organism_tag is not None
    assert "POINTS" in response.organism_tag
    assert "BOSS" in response.organism_tag

    rendered = response.render()
    assert rendered.startswith("[SAGE::C2::CHATGPT]")
    assert "C2 Mission Control" in rendered
    assert "SAGE MISSION CONTROL HUD" in rendered
    assert "C2 operating frame locked onto live repo truth." in rendered


def test_rehydration_fails_closed_without_session_id():
    runtime = _mock_runtime()
    with pytest.raises(ValueError, match="requires a session_id"):
        build_chatgpt_immersion_state(runtime, session_id="")


def test_rehydration_fails_closed_without_runtime_state():
    with pytest.raises(ValueError, match="requires canonical runtime state"):
        build_chatgpt_immersion_state(SimpleNamespace(), session_id="test_sess")
