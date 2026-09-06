import json
from pathlib import Path

from sage.experimental.sports_quant.portfolio import DailySportsPortfolioEngine
from sage.experimental.sports_quant.portfolio_audit import build_diversity_report, render_receipt
from sage.experimental.sports_quant.ingestion import MarketSnapshot, TheOddsApiAdapter
from scripts.execute_sports_portfolio_diversity import main as execute_diversity_script

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
    portfolio = DailySportsPortfolioEngine(target=5, parlay_share=0.20).build(snapshots, "audit-cycle")
    report = build_diversity_report(
        portfolio.records,
        {s.event_id: s.sport for s in snapshots},
        feed_provenance_hash="test_hash_123",
        feed_source="test_source",
    )

    assert portfolio.count == 5
    assert report.total_records == 5
    assert report.unique_events == 4
    assert report.unique_sports == 4
    assert report.unique_market_types == 4
    assert report.unique_event_market_types == 5
    assert report.unique_event_market_lines == 5
    assert report.unique_prediction_ids == 5
    assert report.single_count == 4
    assert report.parlay_count == 1
    assert report.single_unique_events == 4
    assert report.single_unique_sports == 4
    assert report.single_unique_market_types == 3
    assert report.single_unique_event_market_types == 4
    assert report.single_unique_event_market_lines == 4
    assert report.single_unique_prediction_ids == 4
    assert report.feed_provenance_hash == "test_hash_123"
    assert report.feed_source == "test_source"


def test_receipt_render_is_deterministic_json():
    report = build_diversity_report([], {})
    assert render_receipt(report) == '{"feed_provenance_hash":"","feed_source":"","parlay_count":0,"single_count":0,"single_unique_event_market_lines":0,"single_unique_event_market_types":0,"single_unique_events":0,"single_unique_market_types":0,"single_unique_prediction_ids":0,"single_unique_sports":0,"total_records":0,"unique_event_market_lines":0,"unique_event_market_types":0,"unique_events":0,"unique_market_types":0,"unique_prediction_ids":0,"unique_sports":0}'


def test_the_odds_api_adapter_computes_provenance_and_parses_snapshots():
    raw_payload = [
        {
            "id": "e_nfl_001",
            "sport_key": "americanfootball_nfl",
            "commence_time": "2026-09-10T00:20:00Z",
            "home_team": "Chiefs",
            "away_team": "Ravens",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "last_update": "2026-09-05T12:00:00Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Chiefs", "price": -150},
                                {"name": "Ravens", "price": +130},
                            ],
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {"name": "Chiefs", "price": -110, "point": -3.5},
                                {"name": "Ravens", "price": -110, "point": 3.5},
                            ],
                        },
                    ],
                }
            ],
        }
    ]

    snapshots, provenance_hash = TheOddsApiAdapter.parse_response(raw_payload)
    assert len(snapshots) == 2
    assert len(provenance_hash) == 64
    assert snapshots[0].sport == "NFL"
    assert snapshots[0].event_id == "e_nfl_001"
    assert snapshots[0].observed_at_utc == "2026-09-05T12:00:00Z"
    assert snapshots[0].metadata["raw_payload_hash"] == provenance_hash


def test_execute_sports_portfolio_diversity_script_produces_valid_receipt_artifacts():
    exit_code = execute_diversity_script()
    assert exit_code == 0

    p1 = Path("evidence_capture/sports_portfolio_diversity_receipt.json")
    p2 = Path("portfolio_diversity_receipt.json")

    assert p1.exists()
    assert p2.exists()

    d1 = json.loads(p1.read_text(encoding="utf-8"))
    d2 = json.loads(p2.read_text(encoding="utf-8"))

    assert d1 == d2

    expected_keys = {
        "total_records",
        "unique_events",
        "unique_sports",
        "unique_market_types",
        "unique_event_market_types",
        "unique_event_market_lines",
        "unique_prediction_ids",
        "single_count",
        "parlay_count",
        "single_unique_events",
        "single_unique_sports",
        "single_unique_market_types",
        "single_unique_event_market_types",
        "single_unique_event_market_lines",
        "single_unique_prediction_ids",
        "feed_provenance_hash",
        "feed_source",
    }
    assert set(d1.keys()) == expected_keys
    assert d1["total_records"] == 50
    assert d1["single_count"] == 35
    assert d1["parlay_count"] == 15
    assert d1["single_unique_sports"] == 4
    assert d1["single_unique_market_types"] == 3
    assert len(d1["feed_provenance_hash"]) == 64
    assert d1["feed_source"] == "The Odds API (live_market_feed)"
