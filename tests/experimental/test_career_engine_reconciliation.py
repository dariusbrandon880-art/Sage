from sage.experimental.airspace.career_engine import CareerEngine, CareerRank
from sage.experimental.airspace.models import (
    AirspaceState,
    StationID,
    XPCategory,
)


def test_reconcile_reads_canonical_xp_and_qualification_state():
    state = AirspaceState()
    state.game_progression.award_xp(
        station_id=StationID.MISSION_CONTROL,
        category=XPCategory.MISSION_XP,
        amount=120,
        reason="verified mission progress",
        verified_event_ref="commit:test-123",
    )
    state.qualification_registry.promote_station(
        station_id=StationID.MISSION_CONTROL,
        agent_name="GPT",
        qualification_type="CQL",
        target_level=5,
        reason="verified capability",
        evidence_refs=["evidence:cql-5"],
        test_refs=["test:cql-5"],
    )

    projection = CareerEngine().project_station(
        state,
        StationID.MISSION_CONTROL,
        current_rank=CareerRank.CADET,
    )

    assert projection.agent_id == "GPT"
    assert projection.career_xp == 120
    assert projection.cql_level == 5
    assert projection.sql_level == 3
    assert projection.promotion_eligible is False


def test_reconcile_does_not_mutate_canonical_state():
    state = AirspaceState()
    before_xp = state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT)
    before_cql = state.qualification_registry.cql_levels[StationID.ENGINEERING_FLIGHT]

    projection = CareerEngine().project_station(state, StationID.ENGINEERING_FLIGHT)

    assert projection.career_xp == before_xp
    assert projection.cql_level == before_cql
    assert state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT) == before_xp
    assert state.qualification_registry.cql_levels[StationID.ENGINEERING_FLIGHT] == before_cql


def test_reconcile_exposes_all_canonical_stations():
    projections = CareerEngine().reconcile(AirspaceState())

    assert set(projections) == {"Human Director", "GPT", "Gemini", "Jules"}
