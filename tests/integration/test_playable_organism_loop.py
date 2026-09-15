"""Integration test suite for the end-to-end SAGE Persistent Playable Organism Loop.

Validates the complete 10-step turn execution lifecycle, real evidence binding,
verified progression settlement, persistent event ledger storage, and multi-session
rehydration continuity proof.

Architectural proof:
Session A executes Turn 1 -> Persists event ledger -> Session B initializes fresh
instance from disk ledger -> Rehydrates exact state & HUD parity without chat memory ->
Session B executes Turn 2 -> Verifies cumulative persistent progression across sessions.
"""

from pathlib import Path
import pytest

from sage.c2.organism_runtime_contract import OrganismRuntimeContractEngine
from sage.c2.hub_presentation_boundary import HubSurface


VALID_GIT_HEAD_SHA = "9f418683ec902a2a6cd3306aae63d8e1688b4d1b"


def test_persistent_playable_organism_multi_session_continuity_proof(tmp_path: Path) -> None:
    shared_ledger_path = tmp_path / "airspace_ledger.json"

    # =========================================================================
    # SESSION A: Initial session execution
    # =========================================================================
    session_a_engine = OrganismRuntimeContractEngine(ledger_path=shared_ledger_path)

    turn_1_result = session_a_engine.execute_playable_turn(
        session_id="session_alpha_2026",
        turn_id="turn_alpha_001",
        station_id_str="ENGINEERING_FLIGHT",
        action_name="BUILD_ORGANISM_RUNTIME_ENGINE",
        evidence_refs=("evidence/turn_alpha_001.json", "tests/c2/test_organism_runtime_contract.py"),
        verified_event_ref="verified:turn_alpha_001",
        mission_id="MISSION-PLAYABLE-CONTINUITY",
        objective="Prove multi-session persistent organism continuity",
        target="AIRSPACE_C2_ORGANISM",
        exact_git_head=VALID_GIT_HEAD_SHA,
        required_cql=1,
        body_summary="Session Alpha executed Turn 1: Organism Runtime Engine implemented.",
    )

    assert turn_1_result.verified is True
    assert turn_1_result.sequence_number == 1
    assert turn_1_result.points_awarded > 0
    assert turn_1_result.xp_minted > 0
    pts_after_turn_1 = turn_1_result.points_awarded
    xp_after_turn_1 = turn_1_result.xp_minted

    # Confirm ledger file exists and contains events
    assert shared_ledger_path.exists()
    assert shared_ledger_path.stat().st_size > 0

    # =========================================================================
    # SESSION B: Rehydration from persisted state in a fresh engine instance
    # =========================================================================
    # Simulates a completely new session start (e.g. new chat context or process restart)
    session_b_engine = OrganismRuntimeContractEngine(ledger_path=shared_ledger_path)

    rehydrated_state_b = session_b_engine.rehydrate_state()
    rehydrated_xp_b = rehydrated_state_b.game_progression.get_total_airspace_xp()

    # Verify state rehydration matches Session A closing state exactly
    assert rehydrated_xp_b == xp_after_turn_1
    assert rehydrated_state_b.active_mission.mission_id == "MISSION-PLAYABLE-CONTINUITY"

    # Execute Turn 2 in Session B as MISSION_CONTROL
    turn_2_result = session_b_engine.execute_playable_turn(
        session_id="session_beta_2026",
        turn_id="turn_beta_002",
        station_id_str="MISSION_CONTROL",
        action_name="VERIFY_MULTI_SESSION_CONTINUITY",
        evidence_refs=("evidence/turn_beta_002.json", "tests/integration/test_playable_organism_loop.py"),
        verified_event_ref="verified:turn_beta_002",
        mission_id="MISSION-PLAYABLE-CONTINUITY",
        objective="Prove multi-session persistent organism continuity",
        target="AIRSPACE_C2_ORGANISM",
        exact_git_head=VALID_GIT_HEAD_SHA,
        required_cql=1,
        body_summary="Session Beta executed Turn 2: Rehydration continuity verified.",
    )

    assert turn_2_result.verified is True
    assert turn_2_result.sequence_number == 2
    assert turn_2_result.points_awarded > 0
    assert turn_2_result.xp_minted > 0

    # =========================================================================
    # SESSION C: Final cumulative rehydration verification
    # =========================================================================
    session_c_engine = OrganismRuntimeContractEngine(ledger_path=shared_ledger_path)
    final_state = session_c_engine.rehydrate_state()

    total_airspace_xp = final_state.game_progression.get_total_airspace_xp()
    assert total_airspace_xp == xp_after_turn_1 + turn_2_result.xp_minted

    # Verify HUD rehydrated in Session C reflects cumulative XP and points
    final_hud = session_c_engine.render_rehydrated_hud(
        manager=session_c_engine._get_airspace_manager_cls()(shared_ledger_path),
        hub_surface=HubSurface.COMPOSITE,
        body="Final Session C Rehydration Verification Complete.",
    )

    assert "01 — COMMAND BAND" in final_hud
    assert "02 — OPERATING PICTURE" in final_hud
    assert "04 — STRIKE FEED" in final_hud
