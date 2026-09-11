from sage.experimental.sports_quant import DailySportsPortfolioEngine, MarketSnapshot

BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def market(event_id: str) -> MarketSnapshot:
    return MarketSnapshot(
        event_id=event_id,
        sport="NBA",
        league="NBA",
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market="moneyline",
        prices={"home": 2.0, "away": 2.0},
        source="test",
    )


def test_daily_engine_supports_seven_leg_parlays():
    snapshots = [market(f"event-{i}") for i in range(12)]
    portfolio = DailySportsPortfolioEngine(
        target=20,
        min_parlay_legs=7,
        max_parlay_legs=7,
        parlay_share=0.50,
    ).build(snapshots, "daily-seven-leg")

    assert portfolio.parlay_count == 10
    assert all(len(record.legs) == 7 for record in portfolio.records if record.is_parlay)
    assert all(record.market == "parlay" for record in portfolio.records if record.is_parlay)
    assert len({record.selection for record in portfolio.records if record.is_parlay}) == 10
