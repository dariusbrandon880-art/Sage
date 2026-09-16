"""Unit tests for the governed SAGE Organism Runtime Contract."""

from __future__ import annotations

import pytest

from sage.c2.chatgpt_runtime import render_playable_organism_turn
from sage.c2.organism_runtime_contract import (
    DEFAULT_CHATGPT_STATION,
    OrganismRuntimeContractEngine,
    OrganismStationState,
    OrganismTurnReceipt,
    handshake_station_identity,
    resolve_authorized_moves,
)
from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot


class _MockAdapter:
    model_id = "fake-model"
    station = "[SAGE::C2::CHATGPT]"


def _runtime() -> SAGERuntime:
    return SAGERuntime(
        SAGEStateSnapshot(
            state_version="1",
            instance_id="sage-test-instance",
            mission_id="mission-test",
            session_id="session-test",
            authority_scope="director",
            active_frontier="test-frontier",
            stop_boundary="governance",
        )
    )


def _prepare_manager(tmp_path, monkeypatch):
    from sage.experimental.airspace.manager import AirspaceManager
    from sage.experimental.airspace.models import Mission

    monkeypatch.setenv("SAGE_CANONICAL_GIT_SHA", "a" * 40)
    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_path=ledger_file)
    mgr.create_mission(
        actor="TEST",
        mission=Mission(
            mission_id="mission-test",
            mission_name="Organism Test Mission",
            theater="Airspace/C2",
            objective="Validate governed playable-organism continuity",
            assigned_stations=[],
            current_frontier="test-frontier",
        ),
    )
    return mgr


def test_handshake_station_identity_resolves_canonical_state(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
    station_state = handshake_station_identity(manager=mgr, session_id="fresh-session-101")

    assert isinstance(station_state, OrganismStationState)
    assert station_state.station_id == DEFAULT_CHATGPT_STATION
    assert station_state.station_name == "GPT"
    assert len(station_state.provenance_sha) == 40
    assert station_state.rank_level >= 1
    assert isinstance(station_state.rank_title, str)
    assert "RECON" in station_state.authorized_moves
    assert "HUD_PROJECTION" in station_state.authorized_moves
    assert station_state.total_xp == 0
    assert station_state.total_points == 0


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


def test_10_step_playable_turn_execution_success(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
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
    assert receipt.total_xp_after == 100
    assert "COMMAND BAND" in receipt.hud_projection

    events = mgr._load_raw_events()
    event_types = [event["event_type"] for event in events]
    assert "ORGANISM_ACTION_EXECUTED" in event_types
    assert "ORGANISM_EVIDENCE_CAPTURED" in event_types
    assert "XP_AWARDED" in event_types
    assert "POINTS_AWARDED" in event_types
    points_event = next(event for event in events if event["event_type"] == "POINTS_AWARDED")
    assert points_event["payload"]["verified_event_ref"]
    assert points_event["evidence_refs"]


def test_playable_turn_fails_closed_on_unauthorized_move(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
    engine = OrganismRuntimeContractEngine(manager=mgr)

    with pytest.raises(ValueError, match="SAGE move rejection"):
        engine.execute_turn(
            session_id="session-turn-002",
            action_name="UNAUTHORIZED_HYPER_MOVE",
            task="Attempt unauthorized move",
            evidence_refs=("ev_unauthorized",),
        )


def test_playable_turn_fails_closed_without_evidence(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
    engine = OrganismRuntimeContractEngine(manager=mgr)

    with pytest.raises(ValueError, match="Evidence capture requires"):
        engine.execute_turn(
            session_id="session-turn-003",
            action_name="VERIFY",
            task="No evidence",
        )


def test_chatgpt_runtime_render_playable_turn_integration(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
    hud_str, receipt = render_playable_organism_turn(
        session_id="session-gpt-001",
        action_name="ANALYZE",
        task="Reconnaissance analyze frontier",
        evidence_refs=("ev_analyze",),
        manager=mgr,
    )

    assert isinstance(hud_str, str)
    assert receipt.verified is True
    assert receipt.action_executed == "ANALYZE"


def test_handshake_fails_closed_without_git_sha(tmp_path, monkeypatch):
    mgr = _prepare_manager(tmp_path, monkeypatch)
    monkeypatch.delenv("SAGE_CANONICAL_GIT_SHA", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    with pytest.raises(ValueError, match="governed SAGE_CANONICAL_GIT_SHA"):
        handshake_station_identity(manager=mgr, session_id="no-git-sha")


def test_handshake_fails_closed_without_active_mission(tmp_path, monkeypatch):
    from sage.experimental.airspace.manager import AirspaceManager

    monkeypatch.setenv("SAGE_CANONICAL_GIT_SHA", "b" * 40)
    mgr = AirspaceManager(ledger_path=tmp_path / "empty.json")

    with pytest.raises(ValueError, match="active mission required"):
        handshake_station_identity(manager=mgr, session_id="no-mission")
