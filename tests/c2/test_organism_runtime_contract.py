"""Unit tests for SAGE Organism Runtime Contract & Stateful Station Identity Handshake."""

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
from sage.runtime.chatgpt_sage_boundary import SAGEChatGPTBoundary
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


def test_handshake_station_identity_resolves_canonical_state():
    station_state = handshake_station_identity(session_id="fresh-session-101")

    assert isinstance(station_state, OrganismStationState)
    assert station_state.station_id == DEFAULT_CHATGPT_STATION
    assert station_state.station_name == "GPT"
    assert len(station_state.provenance_sha) == 40
    assert station_state.rank_level >= 1
    assert isinstance(station_state.rank_title, str)
    assert "RECON" in station_state.authorized_moves
    assert "HUD_PROJECTION" in station_state.authorized_moves


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


def test_10_step_playable_turn_execution_success(tmp_path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_path=ledger_file)

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


def test_playable_turn_fails_closed_on_unauthorized_move(tmp_path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_path=ledger_file)

    engine = OrganismRuntimeContractEngine(manager=mgr)

    with pytest.raises(ValueError, match="SAGE move rejection"):
        engine.execute_turn(
            session_id="session-turn-002",
            action_name="UNAUTHORIZED_HYPER_MOVE",
            task="Attempt unauthorized move",
        )


def test_chatgpt_runtime_render_playable_turn_integration(tmp_path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_path=ledger_file)

    hud_str, receipt = render_playable_organism_turn(
        session_id="session-gpt-001",
        action_name="ANALYZE",
        task="Reconnaissance analyze frontier",
        manager=mgr,
    )

    assert isinstance(hud_str, str)
    assert receipt.verified is True
    assert receipt.action_executed == "ANALYZE"


def test_chatgpt_boundary_execute_playable_organism_turn(tmp_path):
    from sage.experimental.airspace.manager import AirspaceManager

    ledger_file = tmp_path / "test_ledger.json"
    mgr = AirspaceManager(ledger_path=ledger_file)

    hud_projection, receipt = render_playable_organism_turn(
        session_id="boundary-session-01",
        action_name="HANDSHAKE",
        task="Stateful GPT handshake",
        manager=mgr,
    )

    assert isinstance(hud_projection, str)
    assert receipt.verified is True
    assert receipt.session_id == "boundary-session-01"
    assert receipt.action_executed == "HANDSHAKE"


def test_handshake_fails_closed_without_git_sha(monkeypatch):
    from sage.c2 import organism_runtime_contract

    monkeypatch.setattr(organism_runtime_contract, "_get_canonical_git_sha", lambda: "")

    with pytest.raises(ValueError, match="Organism handshake failed"):
        handshake_station_identity(session_id="no-git-sha")
