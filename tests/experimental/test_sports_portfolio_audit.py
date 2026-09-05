from sage.experimental.sports_quant.portfolio_audit import build_diversity_report, render_receipt
from sage.experimental.sports_quant.prediction import PredictionBatchEngine
from sage.experimental.sports_quant.ingestion import MarketSnapshot

BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def make_snapshot(event_id: str, sport: str, market_type: str, line: float | None) -> MarketSnapshot:
    return MarketSnapshot(
        event_id=event_id,
        sport=sport,
        league=sport,
        event_start_utc=START,
        observed_at_utc=BEFORE,
        market=market_type,
        market_type=market_type,
        line_value=line,
        prices={"home": 1.91},
        source="test",
    )


def test_diversity_receipt_counts_canonical_market_universe_and_parlays_separately():
    specs = [
        ("mlb-001", "MLB", "moneyline", None),
        ("nba-001", "NBA", "spread", -3.5),
        ("nfl-001", "NFL", "spread", -1.5),
        ("nhl-001", "NHL", "total", 6.5),
    ]
    snapshots = [make_snapshot(*spec) for spec in specs]
    engine = PredictionBatchEngine(model_version="audit")
    singles = [engine._generate_one(snapshot, "home", "audit-cycle") for snapshot in snapshots]
    parlay = engine.build_parlay("audit-parent", singles)
    report = build_diversity_report(singles + [parlay], {s.event_id: s.sport for s in snapshots})

    assert report.total_records == 5
    assert report.unique_events == 4
    assert report.unique_sports == 4
    assert report.unique_market_types == 3
    assert report.unique_event_market_types == 4
    assert report.unique_event_market_lines == 4
    assert report.unique_prediction_ids == 5
    assert report.single_count == 4
    assert report.parlay_count == 1
    assert report.single_unique_events == 4
    assert report.single_unique_sports == 4
    assert report.single_unique_market_types == 3
    assert report.single_unique_event_market_types == 4
    assert report.single_unique_event_market_lines == 4
    assert report.single_unique_prediction_ids == 4


def test_receipt_render_is_deterministic_json():
    report = build_diversity_report([], {})
    assert render_receipt(report) == '{"parlay_count":0,"single_count":0,"single_unique_event_market_lines":0,"single_unique_event_market_types":0,"single_unique_events":0,"single_unique_market_types":0,"single_unique_prediction_ids":0,"single_unique_sports":0,"total_records":0,"unique_event_market_lines":0,"unique_event_market_types":0,"unique_events":0,"unique_market_types":0,"unique_prediction_ids":0,"unique_sports":0}'
