import pytest

from sage.experimental.sports_quant import DailySportsPortfolioEngine, MarketSnapshot

BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def market(event_id: str, sport: str, market_name: str, prices: dict[str, float], market_type: str | None = None, line_value: float | None = None) -> MarketSnapshot:
    return MarketSnapshot(event_id=event_id, sport=sport, league=sport, event_start_utc=START, observed_at_utc=BEFORE, market=market_name, market_type=market_type or market_name, line_value=line_value, prices=prices, source="test")


def test_daily_engine_reaches_50_without_duplicate_prediction_identity():
    snapshots = [market(f"mlb-{i}", "MLB", "moneyline", {"home": 2.0, "away": 2.0}) for i in range(20)]
    snapshots += [market(f"nba-{i}", "NBA", "spread", {"home": 1.9, "away": 1.9}, "spread", -3.5) for i in range(20)]
    snapshots += [market(f"nfl-{i}", "NFL", "total", {"over": 1.9, "under": 1.9}, "total", 45.5) for i in range(20)]
    snapshots += [market(f"nhl-{i}", "NHL", "moneyline", {"home": 2.0, "away": 2.0}) for i in range(20)]
    portfolio = DailySportsPortfolioEngine(target=50, parlay_share=0.30).build(snapshots, "daily-2026-09-05")
    assert portfolio.count == 50
    assert portfolio.target_met
    assert portfolio.single_count + portfolio.parlay_count == 50
    assert len({record.prediction_id for record in portfolio.records}) == 50
    assert len({(record.event_id, record.canonical_market_type, record.selection, record.canonical_line_value, record.model_version, record.observed_at_utc) for record in portfolio.records}) == 50
    assert portfolio.parlay_count == 15
    assert portfolio.single_count == 35
    assert all(record.verify_lock() for record in portfolio.records)
    assert all(not record.wagering_executed for record in portfolio.records)
    assert len({record.selection for record in portfolio.records if record.is_parlay}) == portfolio.parlay_count


def test_daily_engine_builds_only_three_to_six_leg_parlays():
    snapshots = [market(f"event-{i}", "NBA", "moneyline", {"home": 2.0, "away": 2.0}) for i in range(10)]
    portfolio = DailySportsPortfolioEngine(target=20, parlay_share=0.50).build(snapshots, "daily-parlay-range")
    assert portfolio.parlay_count == 10
    assert all(3 <= len(record.legs) <= 6 for record in portfolio.records if record.is_parlay)
    assert all(record.market == "parlay" for record in portfolio.records if record.is_parlay)
    assert len({record.selection for record in portfolio.records if record.is_parlay}) == 10


def test_daily_engine_rejects_unknown_sports():
    with pytest.raises(ValueError, match="UNSUPPORTED_SPORTS"):
        DailySportsPortfolioEngine(target=1).build([market("soccer-1", "MLS", "moneyline", {"home": 2.0, "away": 2.0})], "daily-invalid")


def test_daily_engine_fails_closed_when_market_universe_cannot_reach_target():
    snapshots = [market("only-one", "MLB", "moneyline", {"home": 2.0, "away": 2.0})]
    with pytest.raises(ValueError, match="DAILY_TARGET_UNMET"):
        DailySportsPortfolioEngine(target=50).build(snapshots, "daily-too-small")
