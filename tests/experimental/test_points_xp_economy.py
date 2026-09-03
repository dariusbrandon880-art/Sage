from pathlib import Path

import pytest

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID, XPCategory
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy


def manager(tmp_path: Path) -> AirspaceManager:
    return AirspaceManager(tmp_path / "airspace_ledger.json")


def test_base_point_values_are_deterministic():
    assert PointsXPEconomy.base_points(PointEventType.RECON) == 5
    assert PointsXPEconomy.base_points(PointEventType.BUILD) == 25
    assert PointsXPEconomy.base_points(PointEventType.BREAKTHROUGH) == 50
    assert PointsXPEconomy.base_points(PointEventType.REUSE) == 50
    assert PointsXPEconomy.base_points(PointEventType.CAPABILITY_CAPTURE) == 100


def test_verified_points_use_bounded_average_multiplier():
    award = PointsXPEconomy.score_verified_event(
        event_id="evt-001",
        station_id=StationID.MISSION_CONTROL,
        event_type=PointEventType.BUILD,
        verified_event_ref="commit:001",
        evidence_refs=("evidence:001",),
        difficulty=5,
        verification_quality=5,
        impact=5,
        reuse=5,
    )
    assert award.points == 125


def test_points_mint_xp_at_ten_to_one_and_persist(tmp_path: Path):
    m = manager(tmp_path)
    result = PointsXPEconomy.award_verified_event(
        m,
        actor="Mission Control",
        event_id="evt-001",
        station_id=StationID.MISSION_CONTROL,
        event_type=PointEventType.BUILD,
        verified_event_ref="commit:001",
        evidence_refs=("evidence:001",),
        reason="verified build outcome",
        category=XPCategory.MISSION_XP,
        base_points=10,
        difficulty=4,
        verification_quality=4,
        impact=1,
        reuse=1,
    )
    assert result.award.points == 25
    assert result.cumulative_verified_points == 25
    assert result.cumulative_career_xp == 2
    assert result.xp_minted == 2

    rebuilt = m.reconstruct_airspace_state()
    assert rebuilt.game_progression.get_total_xp_for_station(StationID.MISSION_CONTROL) == 2


def test_repeated_verified_event_does_not_double_award(tmp_path: Path):
    m = manager(tmp_path)
    kwargs = dict(
        manager=m,
        actor="Mission Control",
        event_id="evt-001",
        station_id=StationID.MISSION_CONTROL,
        event_type=PointEventType.VERIFICATION,
        verified_event_ref="test:001",
        evidence_refs=("evidence:001",),
        reason="verification",
        category=XPCategory.EVIDENCE_XP,
        base_points=10,
        difficulty=1,
        verification_quality=5,
        impact=1,
        reuse=1,
    )
    first = PointsXPEconomy.award_verified_event(**kwargs)
    second = PointsXPEconomy.award_verified_event(**kwargs)
    assert first.cumulative_verified_points == second.cumulative_verified_points == 20
    assert first.xp_minted == 2
    assert second.xp_minted == 0
    assert len([e for e in m._load_raw_events() if e["event_type"] == "POINTS_AWARDED"]) == 1


def test_unverified_event_cannot_award_points(tmp_path: Path):
    m = manager(tmp_path)
    with pytest.raises(ValueError, match="verified_event_ref"):
        PointsXPEconomy.award_verified_event(
            m,
            actor="Mission Control",
            event_id="evt-001",
            station_id=StationID.MISSION_CONTROL,
            event_type=PointEventType.BUILD,
            verified_event_ref=" ",
            evidence_refs=("evidence:001",),
            reason="bad input",
        )


def test_evidence_is_required_for_points(tmp_path: Path):
    m = manager(tmp_path)
    with pytest.raises(ValueError, match="evidence_refs"):
        PointsXPEconomy.award_verified_event(
            m,
            actor="Mission Control",
            event_id="evt-001",
            station_id=StationID.MISSION_CONTROL,
            event_type=PointEventType.BUILD,
            verified_event_ref="commit:001",
            evidence_refs=(),
            reason="bad input",
        )


def test_points_can_accumulate_across_events_and_retain_remainder(tmp_path: Path):
    m = manager(tmp_path)
    for idx in range(3):
        PointsXPEconomy.award_verified_event(
            m,
            actor="Mission Control",
            event_id=f"evt-{idx}",
            station_id=StationID.MISSION_CONTROL,
            event_type=PointEventType.RECON,
            verified_event_ref=f"evidence:{idx}",
            evidence_refs=(f"evidence:{idx}",),
            reason="verified recon",
            base_points=5,
        )
    raw = m._load_raw_events()
    points = sum(e["payload"]["verified_points"] for e in raw if e["event_type"] == "POINTS_AWARDED")
    assert points == 15
    assert m.reconstruct_airspace_state().game_progression.get_total_xp_for_station(StationID.MISSION_CONTROL) == 1
