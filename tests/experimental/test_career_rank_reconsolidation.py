from sage.experimental.airspace.career_engine import AgentIdentity, CareerEngine
from sage.experimental.airspace.models import AirspaceState, StationID, XPCategory
from sage.experimental.airspace.rank_system import BossClass, BossDisplay, RANK_LADDER, is_c2_rank_title, validate_rank_progression


def test_career_reconciliation_reads_canonical_state_only():
    state = AirspaceState()
    state.game_progression.award_xp(
        station_id=StationID.MISSION_CONTROL,
        category=XPCategory.MISSION_XP,
        amount=120,
        reason="verified mission progress",
        verified_event_ref="commit:test-career-001",
    )
    projection = CareerEngine().project_station(state, StationID.MISSION_CONTROL)
    assert projection.agent_id is AgentIdentity.CHATGPT
    assert projection.career_xp == 120
    assert projection.cql_level == state.qualification_registry.cql_levels[StationID.MISSION_CONTROL]
    assert projection.sql_level == state.qualification_registry.sql_levels[StationID.MISSION_CONTROL]
    assert projection.rank is None


def test_career_reconciliation_is_read_only():
    state = AirspaceState()
    before = state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT)
    CareerEngine().project_station(state, StationID.ENGINEERING_FLIGHT)
    assert state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT) == before


def test_shared_roster_preserves_all_canonical_agents():
    projections = CareerEngine().reconcile(AirspaceState())
    assert set(projections) == {AgentIdentity.DIRECTOR, AgentIdentity.CHATGPT, AgentIdentity.GEMINI, AgentIdentity.JULES}


def test_rank_ladder_has_30_sequential_levels():
    assert len(RANK_LADDER) == 30
    assert [rank.level for rank in RANK_LADDER] == list(range(1, 31))


def test_rank_progression_is_sequential():
    validate_rank_progression(0, 1)
    validate_rank_progression(14, 15)


def test_rank_skipping_is_rejected():
    try:
        validate_rank_progression(1, 3)
    except ValueError as exc:
        assert "skipping" in str(exc).lower()
    else:
        raise AssertionError("rank skipping must be rejected")


def test_c2_is_not_a_rank():
    assert is_c2_rank_title("C2")
    assert not is_c2_rank_title("Master of Operations")


def test_only_big_and_major_boss_classes_exist():
    assert {BossClass.BIG, BossClass.MAJOR} == set(BossClass)
    assert BossDisplay(BossClass.BIG, 2, 3).stars == "⭐"
    assert BossDisplay(BossClass.MAJOR, 2, 3).stars == "⭐⭐"


def test_boss_tallies_are_separate():
    display = BossDisplay(BossClass.BIG, boss_kill_count=3, boss_capture_count=2)
    assert display.kills == "⚔️⚔️⚔️"
    assert display.captures == "┃┃"
