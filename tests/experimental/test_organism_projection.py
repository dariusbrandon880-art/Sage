from sage.experimental.airspace.boss_progression import (
    BOSS_BADGE_CADENCE,
    BossClass,
    BossOutcome,
    BossProgressionAuthority,
)
from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.organism_projection import OrganismProjection
from sage.experimental.airspace.points_xp_economy import PointEventType, PointsXPEconomy


def test_boss_badges_follow_locked_independent_cadence(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    station = StationID.MISSION_CONTROL

    for index in range(20):
        BossProgressionAuthority.record_verified_outcome(
            manager,
            actor="C2",
            outcome=BossOutcome(
                event_id=f"major-kill-{index}",
                station_id=station,
                boss_class=BossClass.MAJOR,
                verified_event_ref=f"major-kill-ref-{index}",
                evidence_refs=(f"evidence-{index}",),
                kill=True,
            ),
            reason="verified Boss outcome",
        )

    for index in range(30):
        BossProgressionAuthority.record_verified_outcome(
            manager,
            actor="C2",
            outcome=BossOutcome(
                event_id=f"big-capture-{index}",
                station_id=station,
                boss_class=BossClass.BIG,
                verified_event_ref=f"big-capture-ref-{index}",
                evidence_refs=(f"capture-evidence-{index}",),
                capture=True,
            ),
            reason="verified Boss outcome",
        )

    progression = BossProgressionAuthority.project_station(manager, station)
    assert BOSS_BADGE_CADENCE[BossClass.MAJOR] == 20
    assert BOSS_BADGE_CADENCE[BossClass.BIG] == 30
    assert progression.major_kills == 20
    assert progression.major_captures == 0
    assert progression.major_badges == 1
    assert progression.big_kills == 0
    assert progression.big_captures == 30
    assert progression.big_badges == 1


def test_kill_and_capture_can_coexist_without_merging_tallies(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    station = StationID.ENGINEERING_FLIGHT
    outcome = BossOutcome(
        event_id="dual-outcome",
        station_id=station,
        boss_class=BossClass.MAJOR,
        verified_event_ref="dual-ref",
        evidence_refs=("dual-evidence",),
        kill=True,
        capture=True,
    )
    BossProgressionAuthority.record_verified_outcome(
        manager, actor="Jules", outcome=outcome, reason="one verified encounter"
    )
    projection = BossProgressionAuthority.project_station(manager, station)
    assert projection.major_kills == 1
    assert projection.major_captures == 1
    assert projection.total_kills == 1
    assert projection.total_captures == 1


def test_duplicate_boss_outcome_is_replay_safe(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    outcome = BossOutcome(
        event_id="duplicate",
        station_id=StationID.INTEL_STATION,
        boss_class=BossClass.BIG,
        verified_event_ref="same-ref",
        evidence_refs=("evidence",),
        kill=True,
    )
    BossProgressionAuthority.record_verified_outcome(
        manager, actor="Gemini", outcome=outcome, reason="first"
    )
    BossProgressionAuthority.record_verified_outcome(
        manager, actor="Gemini", outcome=outcome, reason="replay"
    )
    raw = manager._load_raw_events()
    assert len([e for e in raw if e.get("event_type") == "BOSS_OUTCOME_VERIFIED"]) == 1


def test_organism_projection_joins_points_xp_and_boss_from_one_ledger(tmp_path):
    manager = AirspaceManager(tmp_path / "ledger.json")
    station = StationID.MISSION_CONTROL
    PointsXPEconomy.award_verified_event(
        manager,
        actor="C2",
        event_id="points-1",
        station_id=station,
        event_type=PointEventType.BUILD,
        verified_event_ref="commit-1",
        evidence_refs=("test-1",),
        reason="verified build",
        difficulty=2,
        verification_quality=2,
        impact=2,
        reuse=2,
    )
    BossProgressionAuthority.record_verified_outcome(
        manager,
        actor="C2",
        outcome=BossOutcome(
            event_id="boss-1",
            station_id=station,
            boss_class=BossClass.BIG,
            verified_event_ref="boss-ref-1",
            evidence_refs=("boss-evidence-1",),
            kill=True,
        ),
        reason="verified Boss outcome",
    )

    state = manager.reconstruct_airspace_state()
    projection = OrganismProjection.project_station(manager, state, station)
    assert projection.points == 25 * 2
    assert projection.career_xp == 5
    assert projection.boss.big_kills == 1
    assert projection.boss.total_captures == 0
    assert "POINTS 50" in OrganismProjection.render_agent_tag(projection)
    assert "XP 5" in OrganismProjection.render_agent_tag(projection)
    assert "⚔️ 1" in OrganismProjection.render_agent_tag(projection)
