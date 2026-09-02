from sage.experimental.airspace.career_engine import AgentIdentity, CareerEngine
from sage.experimental.airspace.models import AirspaceState, StationID, XPCategory


def test_reconcile_reads_canonical_agent_progression_and_qualification():
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

    projection = CareerEngine().project_station(state, StationID.MISSION_CONTROL)

    assert projection.agent_id is AgentIdentity.CHATGPT
    assert projection.station_id is StationID.MISSION_CONTROL
    assert projection.career_xp == 120
    assert projection.cql_level == 5
    assert projection.sql_level == 3
    assert projection.rank is None


def test_reconcile_is_read_only():
    state = AirspaceState()
    before_xp = state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT)
    before_cql = state.qualification_registry.cql_levels[StationID.ENGINEERING_FLIGHT]
    before_sql = state.qualification_registry.sql_levels[StationID.ENGINEERING_FLIGHT]

    projection = CareerEngine().project_station(state, StationID.ENGINEERING_FLIGHT)

    assert projection.career_xp == before_xp
    assert projection.cql_level == before_cql
    assert projection.sql_level == before_sql
    assert state.game_progression.get_total_xp_for_station(StationID.ENGINEERING_FLIGHT) == before_xp
    assert state.qualification_registry.cql_levels[StationID.ENGINEERING_FLIGHT] == before_cql
    assert state.qualification_registry.sql_levels[StationID.ENGINEERING_FLIGHT] == before_sql


def test_reconcile_preserves_agent_attribution_and_shared_roster():
    projections = CareerEngine().reconcile(AirspaceState())

    assert set(projections) == {
        AgentIdentity.DIRECTOR,
        AgentIdentity.CHATGPT,
        AgentIdentity.GEMINI,
        AgentIdentity.JULES,
    }
    assert projections[AgentIdentity.CHATGPT].station_id is StationID.MISSION_CONTROL
    assert projections[AgentIdentity.GEMINI].station_id is StationID.INTEL_STATION
    assert projections[AgentIdentity.JULES].station_id is StationID.ENGINEERING_FLIGHT


def test_unknown_rank_is_not_invented_by_reconciliation():
    projection = CareerEngine().project_station(AirspaceState(), StationID.MISSION_CONTROL)

    assert projection.rank is None
