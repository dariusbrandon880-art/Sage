"""Unit test suite for SAGE OrganismRuntimeContractEngine.

Validates the complete 10-step interaction loop:
SENSE -> REHYDRATE -> IDENTITY LOCK -> MISSION RESOLUTION -> MOVE AUTHORIZATION ->
ACTION -> EVIDENCE -> REWARD -> STATE UPDATE -> REHYDRATED HUD.

Enforces fail-closed anti-fabrication boundaries, qualification checks, evidence requirements,
durable XP/points settlement, and exact Git HEAD SHA binding.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from sage.c2.chatgpt_runtime import execute_playable_organism_turn, rehydrate_playable_organism_state, render_playable_organism_turn
from sage.c2.organism_runtime_contract import (
    DEFAULT_CHATGPT_STATION,
    OrganismRuntimeContractEngine,
    OrganismStationState,
    OrganismTurnReceipt,
    PlayableTurnResult,
    handshake_station_identity,
    resolve_authorized_moves,
)


VALID_GIT_HEAD_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e"


def test_handshake_station_identity_resolves_canonical_state():
    station_state = handshake_station_identity(session_id="fresh-session-101", station_id="[SAGE::C2::CHATGPT]")

    assert isinstance(station_state, OrganismStationState)
    assert station_state.station_id == DEFAULT_CHATGPT_STATION
    assert station_state.station_name == "GPT"
    assert len(station_state.provenance_sha) == 40
    assert station_state.rank_level >= 1
    assert isinstance(station_state.rank_title, str)
    assert "RECON" in station_state.authorized_moves
    assert "HUD_PROJECTION" in station_state.authorized_moves


def test_handshake_rejects_unverified_station_id():
    with pytest.raises(ValueError, match="Unknown or unverified station_id"):
        handshake_station_identity(session_id="bad-st", station_id="INVALID_STATION_NAME")


def test_qualification_conditioned_authorized_moves():
    moves_cql0 = resolve_authorized_moves(cql=0)
    assert "RECON" in moves_cql0
    assert "VERIFY" not in moves_cql0

    moves_cql2 = resolve_authorized_moves(cql=2)
    assert "RECON" in moves_cql2
    assert "VERIFY" in moves_cql2
    assert "EXECUTE_ACTION" not in moves_cql2

    moves_cql3 = resolve_authorized_moves(cql=3)
    assert "EXECUTE_ACTION" in moves_cql3
    assert "ADJUDICATE_PROGRESSION" in moves_cql3


def test_10_step_playable_turn_execution_success(tmp_path: Path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_file)

    engine = OrganismRuntimeContractEngine(manager=mgr)
    receipt = engine.execute_turn(
        session_id="session-turn-001",
        action_name="VERIFY",
        task="Verify C2 HUD continuity",
        evidence_refs=("ev_001", "ev_002"),
        xp_award=100,
        points_award=50,
    )

    assert isinstance(receipt, OrganismTurnReceipt)
    assert receipt.verified is True
    assert receipt.action_executed == "VERIFY"
    assert receipt.xp_minted == 100
    assert receipt.points_awarded == 50
    assert len(receipt.evidence_digest) == 64
    assert len(receipt.provenance_sha) == 40
    assert "COMMAND BAND" in receipt.hud_projection or "C2 MISSION CONTROL" in receipt.hud_projection

    # Verify that the persisted POINTS_AWARDED event contains both verified_event_ref and evidence_refs
    raw_events = mgr._load_raw_events()
    points_event = next((e for e in raw_events if e.get("event_type") == "POINTS_AWARDED"), None)
    assert points_event is not None
    assert points_event["payload"]["verified_event_ref"] == receipt.evidence_digest
    assert points_event["evidence_refs"] == ["ev_001", "ev_002"]


def test_playable_turn_fails_closed_on_unauthorized_move(tmp_path: Path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_file)

    engine = OrganismRuntimeContractEngine(manager=mgr)

    with pytest.raises(ValueError, match="SAGE move rejection"):
        engine.execute_turn(
            session_id="session-turn-002",
            action_name="UNAUTHORIZED_HYPER_MOVE",
            task="Attempt unauthorized move",
        )


def test_playable_turn_with_real_executor(tmp_path: Path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_file)

    executed = []

    def my_executor():
        executed.append("REAL_ACTION_DONE")
        return "Executed custom real action"

    engine = OrganismRuntimeContractEngine(manager=mgr)
    receipt = engine.execute_turn(
        session_id="session-exec-01",
        action_name="VERIFY",
        task="Real action test",
        evidence_refs=("ev_real_01",),
        executor=my_executor,
    )

    assert executed == ["REAL_ACTION_DONE"]
    assert receipt.verified is True


def test_playable_turn_10_step_execution_engine(tmp_path: Path) -> None:
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


def test_playable_turn_qualification_failure_fails_closed(tmp_path: Path) -> None:
    ledger = tmp_path / "airspace_ledger.json"
    engine = OrganismRuntimeContractEngine(ledger_path=ledger)

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


def test_chatgpt_runtime_render_playable_turn_integration(tmp_path: Path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_file)

    hud_str, receipt = render_playable_organism_turn(
        session_id="session-gpt-001",
        action_name="ANALYZE",
        task="Reconnaissance analyze frontier",
        manager=mgr,
    )

    assert isinstance(hud_str, str)
    assert receipt.verified is True
    assert receipt.action_executed == "ANALYZE"
