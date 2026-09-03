from pathlib import Path

import pytest

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.points_xp_economy import PointEventType
from sage.experimental.airspace.turn_engine import TurnContribution, TurnEngine, TurnStatus


def manager(tmp_path: Path) -> AirspaceManager:
    return AirspaceManager(tmp_path / "airspace_ledger.json")


def contribution(contribution_id: str, station_id: StationID, role: str) -> TurnContribution:
    return TurnContribution(
        contribution_id=contribution_id,
        station_id=station_id,
        role=role,
        evidence_refs=(f"evidence:{contribution_id}",),
        artifact_refs=(f"artifact:{contribution_id}",),
    )


def test_turn_resolves_verified_points_xp_and_fresh_hud(tmp_path: Path) -> None:
    mgr = manager(tmp_path)
    engine = TurnEngine(mgr)

    sequence = engine.open_turn(
        actor="Mission Control",
        turn_id="turn-001",
        input_ref="input:001",
    )
    assert sequence == 1

    resolution = engine.resolve_turn(
        actor="Mission Control",
        turn_id="turn-001",
        event_type=PointEventType.BUILD,
        verified_event_ref="verified:turn-001",
        evidence_refs=("evidence:turn-001",),
        contributions=(
            contribution("c-gpt", StationID.MISSION_CONTROL, "BUILT"),
            contribution("c-jules", StationID.ENGINEERING_FLIGHT, "VERIFIED"),
        ),
        reason="Verified turn outcome",
        difficulty=2,
        verification_quality=5,
        impact=3,
        reuse=2,
    )

    assert resolution.status is TurnStatus.CLOSED
    assert resolution.verified is True
    # The canonical economy scores BUILD at 25 * (2 + 5 + 3 + 2) / 4 = 75.
    assert resolution.total_verified_points == 75
    assert sum(r.award.points for r in resolution.contribution_results) == 75
    assert resolution.total_xp_minted == 7
    assert mgr.reconstruct_airspace_state().game_progression.get_total_xp_for_station(
        StationID.MISSION_CONTROL
    ) == 3
    assert "POINTS 38" in engine.render_hud(StationID.MISSION_CONTROL)
    assert "XP 3" in engine.render_hud(StationID.MISSION_CONTROL)


def test_turn_requires_evidence(tmp_path: Path) -> None:
    mgr = manager(tmp_path)
    engine = TurnEngine(mgr)
    engine.open_turn(actor="Mission Control", turn_id="turn-002", input_ref="input:002")

    with pytest.raises(ValueError, match="verified event reference and evidence"):
        engine.resolve_turn(
            actor="Mission Control",
            turn_id="turn-002",
            event_type=PointEventType.RECON,
            verified_event_ref="",
            evidence_refs=(),
            contributions=(contribution("c", StationID.MISSION_CONTROL, "DISCOVERED"),),
            reason="No proof",
        )


def test_turn_cannot_be_resolved_twice(tmp_path: Path) -> None:
    mgr = manager(tmp_path)
    engine = TurnEngine(mgr)
    engine.open_turn(actor="Mission Control", turn_id="turn-003", input_ref="input:003")
    kwargs = dict(
        actor="Mission Control",
        turn_id="turn-003",
        event_type=PointEventType.RECON,
        verified_event_ref="verified:turn-003",
        evidence_refs=("evidence:turn-003",),
        contributions=(contribution("c", StationID.MISSION_CONTROL, "DISCOVERED"),),
        reason="Verified recon",
    )
    engine.resolve_turn(**kwargs)
    with pytest.raises(ValueError, match="is not open"):
        engine.resolve_turn(**kwargs)


def test_turn_causal_parent_and_settlement_id_are_deterministic(tmp_path: Path) -> None:
    mgr = manager(tmp_path)
    engine = TurnEngine(mgr)
    engine.open_turn(actor="Mission Control", turn_id="turn-parent", input_ref="input:parent")
    engine.open_turn(
        actor="Mission Control",
        turn_id="turn-child",
        input_ref="input:child",
        parent_turn_ids=("turn-parent",),
    )
    resolution = engine.resolve_turn(
        actor="Mission Control",
        turn_id="turn-child",
        event_type=PointEventType.RECON,
        verified_event_ref="verified:child",
        evidence_refs=("evidence:child",),
        contributions=(contribution("c", StationID.MISSION_CONTROL, "DISCOVERED"),),
        reason="Verified causal child",
    )
    assert resolution.settlement_id == engine._settlement_id("turn-child", "verified:child")
    assert len(resolution.settlement_id) == 64


def test_turn_rejects_duplicate_settlement_identity(tmp_path: Path) -> None:
    mgr = manager(tmp_path)
    engine = TurnEngine(mgr)
    engine.open_turn(actor="Mission Control", turn_id="turn-a", input_ref="input:a")
    kwargs = dict(
        actor="Mission Control",
        turn_id="turn-a",
        event_type=PointEventType.RECON,
        verified_event_ref="verified:a",
        evidence_refs=("evidence:a",),
        contributions=(contribution("c", StationID.MISSION_CONTROL, "DISCOVERED"),),
        reason="Verified recon",
    )
    engine.resolve_turn(**kwargs)
    with pytest.raises(ValueError, match="is not open"):
        engine.resolve_turn(**kwargs)
