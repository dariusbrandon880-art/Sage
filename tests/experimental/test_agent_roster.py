from sage.experimental.agent_roster import build_default_roster, build_roster_nameplates


def test_default_roster_contains_all_operating_stations_at_cql_zero():
    roster = build_default_roster()
    assert set(roster) == {
        "mission_director",
        "agent_c2",
        "agent_gemini",
        "agent_jules",
        "sensor_super_search",
    }
    assert all(agent.rank.value == "CQL-0" and agent.xp == 0 for agent in roster.values())


def test_roster_nameplates_are_glanceable_and_truthful():
    badges = build_roster_nameplates()
    assert [badge.display_name for badge in badges] == [
        "Mission Director",
        "C2",
        "Gemini",
        "Jules",
        "Super Search",
    ]
    assert all(badge.rank == "CQL-0" for badge in badges)
    assert all("XP" in badge.compact() for badge in badges)
