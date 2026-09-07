"""Unit tests for ChatGPT whole-organism immersion rehydration."""

from types import SimpleNamespace
import pytest

from sage.c2.immersion_rehydration import (
    C2_OPERATING_FRAME_SEQUENCE,
    REHYDRATE_HUD_COMMAND,
    REHYDRATION_CONTRACT_VERSION,
    REQUIRED_FRAME_COMPONENTS,
    WHOLE_ORGANISM_IMMERSION_CONTRACT,
    build_chatgpt_immersion_state,
    build_chatgpt_whole_organism_frame,
    is_rehydrate_hud_command,
    normalize_c2_command,
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
    assert C2_OPERATING_FRAME_SEQUENCE == (
        "LIVE REPO",
        "FULL WORKFLOW RECON",
        "CANONICAL ARCHITECTURE",
        "ACTIVE FRONTIER",
        "ENGINEER",
        "TEST",
        "EVIDENCE",
        "VERIFY",
        "PROMOTE",
    )
    assert state.provenance_head is not None
    assert len(state.provenance_head) == 64


def test_whole_organism_frame_contains_one_coupled_interface_contract():
    frame = build_chatgpt_whole_organism_frame(_mock_runtime(), session_id="fresh_chat_001")

    assert frame["contract"] == WHOLE_ORGANISM_IMMERSION_CONTRACT
    assert frame["contract_version"] == "2"
    assert frame["station_identity"] == "[SAGE::C2::CHATGPT]"
    assert tuple(frame["operating_frame"]) == C2_OPERATING_FRAME_SEQUENCE
    assert frame["immersion"]["read_only"] is True
    assert frame["immersion"]["nameplate_required"] is True
    assert frame["immersion"]["hud_continuity_required"] is True
    assert tuple(frame["required_components"]) == REQUIRED_FRAME_COMPONENTS
    assert frame["provenance_head"]


def test_fresh_chat_rehydration_does_not_depend_on_previous_session_memory():
    runtime = _mock_runtime()

    first = build_chatgpt_whole_organism_frame(runtime, session_id="fresh_chat_A")
    second = build_chatgpt_whole_organism_frame(runtime, session_id="fresh_chat_B")

    assert first["station_identity"] == second["station_identity"] == "[SAGE::C2::CHATGPT]"
    assert first["canonical_state"]["mission"] == second["canonical_state"]["mission"]
    assert first["canonical_state"]["next_move"] == second["canonical_state"]["next_move"]
    assert first["operating_frame"] == second["operating_frame"]
    assert first["provenance_head"] != second["provenance_head"]


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


def test_rehydrate_hud_command_is_canonical_and_whitespace_tolerant():
    assert REHYDRATE_HUD_COMMAND == "rehydrate hud"
    assert REHYDRATION_CONTRACT_VERSION == "2"
    assert normalize_c2_command("  REHYDRATE   HUD  ") == REHYDRATE_HUD_COMMAND
    assert is_rehydrate_hud_command("REHYDRATE HUD")
    assert is_rehydrate_hud_command("  rehydrate   hud ")
    assert not is_rehydrate_hud_command("rehydrate")
    assert not is_rehydrate_hud_command("rehydrate hud now")
    assert not is_rehydrate_hud_command("show hud")


def test_rehydration_fails_closed_without_session_id():
    runtime = _mock_runtime()
    with pytest.raises(ValueError, match="requires a session_id"):
        build_chatgpt_immersion_state(runtime, session_id="")


def test_rehydration_fails_closed_without_runtime_state():
    with pytest.raises(ValueError, match="requires canonical runtime state"):
        build_chatgpt_immersion_state(SimpleNamespace(), session_id="test_sess")


def test_rehydration_fails_closed_when_runtime_is_not_rehydrated():
    runtime = _mock_runtime()
    runtime.get_status = lambda: {"c2_status": {"rehydrated": False}}
    with pytest.raises(ValueError, match="not rehydrated"):
        build_chatgpt_immersion_state(runtime, session_id="test_sess")
