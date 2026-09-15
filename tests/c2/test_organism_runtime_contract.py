"""Unit test suite for SAGE OrganismRuntimeContractEngine.

Validates the complete 10-step interaction loop:
SENSE -> REHYDRATE -> IDENTITY LOCK -> MISSION RESOLUTION -> MOVE AUTHORIZATION ->
ACTION -> EVIDENCE -> REWARD -> STATE UPDATE -> REHYDRATED HUD.

Enforces fail-closed anti-fabrication boundaries, qualification checks, evidence requirements,
and exact Git HEAD SHA binding.
"""

from pathlib import Path
import pytest

from sage.c2.organism_runtime_contract import OrganismRuntimeContractEngine, PlayableTurnResult
from sage.c2.chatgpt_runtime import execute_playable_organism_turn, rehydrate_playable_organism_state


VALID_GIT_HEAD_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e"


def test_playable_turn_10_step_execution(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"
    engine = OrganismRuntimeContractEngine(ledger_path=ledger)

    result = engine.execute_playable_turn(
        session_id="session_test_001",
        turn_id="turn_unit_001",
        station_id_str="ENGINEERING_FLIGHT",
        action_name="EXECUTE_BOUNDED_TURN",
        evidence_refs=("evidence/test_001.json",),
        verified_event_ref="verified:turn_unit_001",
        exact_git_head=VALID_GIT_HEAD_SHA,
        required_cql=1,
        body_summary="Unit test playable turn executed",
    )

    assert isinstance(result, PlayableTurnResult)
    assert result.turn_id == "turn_unit_001"
    assert result.sequence_number == 1
    assert result.station_id == "ENGINEERING_FLIGHT"
    assert result.agent_name == "Jules"
    assert result.verified is True
    assert result.points_awarded > 0
    assert result.xp_minted > 0
    assert result.rank_level >= 1
    assert isinstance(result.rank_title, str)
    assert len(result.evidence_digest) == 64
    assert result.git_head_sha == VALID_GIT_HEAD_SHA

    # Verify HUD presentation structure contains visual Control Tower headers
    hud = result.rehydrated_hud
    assert "01 — COMMAND BAND" in hud
    assert "02 — OPERATING PICTURE" in hud
    assert "04 — STRIKE FEED" in hud
    assert "05 — ORGANISM PROGRESSION" in hud or "SAGE ORGANISM" in hud


def test_playable_turn_qualification_failure_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"
    engine = OrganismRuntimeContractEngine(ledger_path=ledger)

    # Engineering station has default CQL-4, SQL-2. Requesting CQL-7 must fail closed.
    with pytest.raises(PermissionError, match="Requires CQL-7"):
        engine.execute_playable_turn(
            session_id="session_test_002",
            turn_id="turn_unit_002",
            station_id_str="ENGINEERING_FLIGHT",
            action_name="SUPER_FRONTIER_STRIKE",
            evidence_refs=("evidence/test_002.json",),
            verified_event_ref="verified:turn_unit_002",
            exact_git_head=VALID_GIT_HEAD_SHA,
            required_cql=7,
        )


def test_playable_turn_missing_evidence_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"
    engine = OrganismRuntimeContractEngine(ledger_path=ledger)

    with pytest.raises(ValueError, match="evidence_refs cannot be empty"):
        engine.execute_playable_turn(
            session_id="session_test_003",
            turn_id="turn_unit_003",
            station_id_str="ENGINEERING_FLIGHT",
            action_name="EXECUTE_UNEVIDENCED_TURN",
            evidence_refs=(),
            verified_event_ref="verified:turn_unit_003",
            exact_git_head=VALID_GIT_HEAD_SHA,
        )


def test_playable_turn_invalid_git_sha_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"
    engine = OrganismRuntimeContractEngine(ledger_path=ledger)

    with pytest.raises(ValueError, match="Invalid git HEAD commit SHA"):
        engine.sense_environment(exact_git_head="short_sha_123")


def test_chatgpt_runtime_wrapper_functions(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"

    result = execute_playable_organism_turn(
        session_id="session_test_wrapper",
        turn_id="turn_wrapper_001",
        station_id="MISSION_CONTROL",
        action_name="SYNTHESIZE_C2_STATE",
        evidence_refs=("evidence/wrapper_001.json",),
        verified_event_ref="verified:wrapper_001",
        ledger_path=ledger,
        exact_git_head=VALID_GIT_HEAD_SHA,
        body_summary="ChatGPT runtime wrapper playable turn",
    )

    assert result.turn_id == "turn_wrapper_001"
    assert result.station_id == "MISSION_CONTROL"
    assert result.agent_name == "GPT"
    assert result.points_awarded > 0

    rehydrated = rehydrate_playable_organism_state(ledger_path=ledger)
    assert rehydrated.game_progression.get_total_airspace_xp() > 0
