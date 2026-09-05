from sage.experimental.sports_quant import FanDuelSnapshotAdapter, MarketSnapshot, PlayerPropSnapshot
from sage.experimental.sports_quant.portfolio import DailySportsPortfolioEngine
from sage.experimental.sports_quant.prediction import FanDuelPlayerPropAnalyzer, PredictionBatchEngine, PredictionRecord

BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def snapshot(market: str, market_type: str, line_value: float | None) -> MarketSnapshot:
    return MarketSnapshot(event_id="nba-001", sport="NBA", league="NBA", event_start_utc=START, observed_at_utc=BEFORE, market=market, market_type=market_type, line_value=line_value, prices={"home": 1.91, "away": 1.91}, source="test")


def test_same_event_distinguishes_market_type_and_line_value():
    moneyline = snapshot("moneyline", "moneyline", None)
    spread = snapshot("spread", "spread", -3.5)
    alternate = snapshot("alternate_spread", "spread", -1.5)
    assert moneyline.market_identity != spread.market_identity
    assert spread.market_identity != alternate.market_identity


def test_mapping_parses_explicit_market_type_and_line_value():
    result = FanDuelSnapshotAdapter.from_mapping({"event": {"id": "nba-002", "sport": "NBA", "league": "NBA", "start_utc": START}, "market": {"name": "alternate_spread", "type": "spread", "line_value": -3.5, "prices": {"home": 1.91, "away": 1.91}}, "observed_at_utc": BEFORE})
    assert result.canonical_market_type == "spread"
    assert result.canonical_line_value == "-3.5"


def test_prediction_ids_are_distinct_for_market_type_and_line():
    engine = PredictionBatchEngine(model_version="identity")
    records = [engine._generate_one(snapshot("spread", "spread", line), "home", "cycle-001") for line in (-3.5, -1.5)]
    assert records[0].prediction_id != records[1].prediction_id
    assert records[0].canonical_line_value == "-3.5"
    assert records[1].canonical_line_value == "-1.5"


def test_prediction_identity_builder_normalizes_market_type_and_line():
    prediction_id = PredictionRecord.build_prediction_id(cycle_id="cycle-002", event_id="nba-003", market_type=" SPREAD ", selection="home", line_value=-3.5)
    assert prediction_id == "pred_cycle-002_nba-003_spread_home_-3.5"


def test_portfolio_dedup_keeps_distinct_lines_and_rejects_exact_duplicates():
    engine = PredictionBatchEngine(model_version="portfolio-identity")
    records = [engine._generate_one(snapshot("spread", "spread", line), "home", "cycle-003") for line in (-3.5, -1.5)]
    unique, rejected = DailySportsPortfolioEngine._dedupe(records + [records[0]])
    assert len(unique) == 2
    assert rejected == 1
    assert {record.canonical_line_value for record in unique} == {"-3.5", "-1.5"}


def test_player_prop_identity_separates_category_and_threshold():
    points = PlayerPropSnapshot(event_id="nba-prop-001", sport="NBA", league="NBA", event_start_utc=START, observed_at_utc=BEFORE, player_name="Player A", prop_category="points", threshold=20.0, prices={"over": 1.9, "under": 1.9})
    rebounds = PlayerPropSnapshot(event_id="nba-prop-001", sport="NBA", league="NBA", event_start_utc=START, observed_at_utc=BEFORE, player_name="Player A", prop_category="rebounds", threshold=20.0, prices={"over": 1.9, "under": 1.9})
    analyzer = FanDuelPlayerPropAnalyzer(model_version="prop-identity")
    a = analyzer.generate_prop_prediction(points, analyzer.analyze_prop(points), "cycle-prop")
    b = analyzer.generate_prop_prediction(rebounds, analyzer.analyze_prop(rebounds), "cycle-prop")
    assert a.prediction_id != b.prediction_id
    assert a.market_type == b.market_type == "player_prop"
    assert a.line_value == b.line_value == 20.0
    assert a.selection != b.selection
    assert a.verify_lock() and b.verify_lock()


def test_parlay_selection_uses_stable_leg_prediction_ids():
    engine = PredictionBatchEngine(model_version="parlay-identity")
    legs = [engine._generate_one(snapshot(f"market-{i}", "spread", float(-i)), "home", "cycle-parlay") for i in range(1, 4)]
    parent = engine.build_parlay("daily-stable", legs)
    assert parent.selection == " + ".join(leg.prediction_id for leg in legs)
    assert parent.legs == tuple(leg.prediction_id for leg in legs)
    assert parent.market_type == "parlay"
    assert parent.verify_lock()


def test_target_met_uses_configured_target():
    portfolio = DailySportsPortfolioEngine(target=1).build([snapshot("moneyline", "moneyline", None)], "target-aware")
    assert portfolio.target == 1
    assert portfolio.target_met
