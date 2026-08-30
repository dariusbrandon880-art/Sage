from sage.experimental.airspace.sports_adapter import (
    CANONICAL_SPORT_COMPETITIONS,
    SportsRCEAirspaceAdapter,
)


def test_canonical_boundary_contains_declared_multi_sport_frontier():
    boundary = SportsRCEAirspaceAdapter.canonical_boundary()
    assert boundary["sports"] == {
        sport: list(competitions)
        for sport, competitions in sorted(CANONICAL_SPORT_COMPETITIONS.items())
    }
    assert "MLB" in boundary["sports"]["baseball"]
    assert set(("NBA", "WNBA", "NCAAB")) <= set(boundary["sports"]["basketball"])
    assert set(("NFL", "NCAAF")) <= set(boundary["sports"]["football"])
    assert "NHL" in boundary["sports"]["hockey"]
    assert set(("ATP", "WTA")) <= set(boundary["sports"]["tennis"])


def test_known_competitions_are_accepted():
    for sport, competitions in CANONICAL_SPORT_COMPETITIONS.items():
        for competition in competitions:
            assert SportsRCEAirspaceAdapter.validate_competition(sport, competition)


def test_unknown_non_extensible_competition_fails_closed():
    assert not SportsRCEAirspaceAdapter.validate_competition("baseball", "FAKE-LEAGUE")
    assert not SportsRCEAirspaceAdapter.validate_competition("basketball", "FAKE-LEAGUE")


def test_soccer_is_extensible_but_not_empty():
    assert SportsRCEAirspaceAdapter.validate_competition("soccer", "Premier League")
    assert not SportsRCEAirspaceAdapter.validate_competition("soccer", "")
