from sage.experimental.sports_quant import FanDuelSnapshotAdapter, MarketSnapshot


BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def test_same_event_distinguishes_market_type_and_line_value():
    moneyline = MarketSnapshot(
        event_id="mlb-001",
        sport="MLB",
        league="MLB",
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market="moneyline",
        market_type="moneyline",
        line_value=None,
        prices={"home": 2.0, "away": 2.0},
        source="test",
    )
    run_line = MarketSnapshot(
        event_id="mlb-001",
        sport="MLB",
        league="MLB",
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market="run_line",
        market_type="spread",
        line_value=-1.5,
        prices={"home": 1.9, "away": 1.9},
        source="test",
    )
    team_total = MarketSnapshot(
        event_id="mlb-001",
        sport="MLB",
        league="MLB",
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market="team_total",
        market_type="team_total",
        line_value=4.5,
        prices={"over": 1.9, "under": 1.9},
        source="test",
    )

    assert moneyline.market_identity != run_line.market_identity
    assert run_line.market_identity != team_total.market_identity
    assert moneyline.canonical_market_type == "moneyline"
    assert run_line.canonical_line_value == "-1.5"
    assert team_total.canonical_line_value == "4.5"


def test_mapping_parses_explicit_market_type_and_line_value():
    snapshot = FanDuelSnapshotAdapter.from_mapping({
        "event": {"id": "nba-001", "sport": "NBA", "league": "NBA", "start_utc": START},
        "market": {
            "name": "alternate_spread",
            "type": "spread",
            "line_value": -3.5,
            "prices": {"home": 1.91, "away": 1.91},
        },
        "observed_at_utc": BEFORE,
    })

    assert snapshot.canonical_market_type == "spread"
    assert snapshot.canonical_line_value == "-3.5"
    assert snapshot.market_identity == ("nba-001", "spread", "-3.5", BEFORE)
