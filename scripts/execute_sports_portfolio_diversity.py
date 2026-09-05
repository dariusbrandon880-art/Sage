#!/usr/bin/env python3
"""Execute SAGE Sports Portfolio Diversity Audit and Receipt Generation.

Constructs a multi-sport market snapshot universe, builds a 50-prediction portfolio,
audits the canonical eight diversity metrics and single-only diversity metrics, and
persists deterministic JSON receipts to evidence_capture/sports_portfolio_diversity_receipt.json
and portfolio_diversity_receipt.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.experimental.sports_quant import (  # noqa: E402
    DailySportsPortfolioEngine,
    MarketSnapshot,
)
from sage.experimental.sports_quant.portfolio_audit import (  # noqa: E402
    build_diversity_report,
    render_receipt,
)

BEFORE = "2026-09-05T12:00:00+00:00"
START = "2026-09-05T20:00:00+00:00"


def make_market_universe() -> list[MarketSnapshot]:
    snapshots = []
    # Interleave 20 MLB, 20 NBA, 20 NFL, 20 NHL games
    for i in range(20):
        snapshots.append(
            MarketSnapshot(
                event_id=f"mlb-2026-{i:03d}",
                sport="MLB",
                league="MLB",
                event_start_utc=START,
                observed_at_utc=BEFORE,
                market="moneyline",
                market_type="moneyline",
                line_value=None,
                prices={"home": 1.95, "away": 1.90},
                source="fanduel",
            )
        )
        snapshots.append(
            MarketSnapshot(
                event_id=f"nba-2026-{i:03d}",
                sport="NBA",
                league="NBA",
                event_start_utc=START,
                observed_at_utc=BEFORE,
                market="spread",
                market_type="spread",
                line_value=-4.5 + (i % 5),
                prices={"home": 1.91, "away": 1.91},
                source="fanduel",
            )
        )
        snapshots.append(
            MarketSnapshot(
                event_id=f"nfl-2026-{i:03d}",
                sport="NFL",
                league="NFL",
                event_start_utc=START,
                observed_at_utc=BEFORE,
                market="total",
                market_type="total",
                line_value=42.5 + (i % 7),
                prices={"over": 1.91, "under": 1.91},
                source="fanduel",
            )
        )
        snapshots.append(
            MarketSnapshot(
                event_id=f"nhl-2026-{i:03d}",
                sport="NHL",
                league="NHL",
                event_start_utc=START,
                observed_at_utc=BEFORE,
                market="moneyline",
                market_type="moneyline",
                line_value=None,
                prices={"home": 2.10, "away": 1.75},
                source="fanduel",
            )
        )
    return snapshots


def main() -> int:
    print("=" * 70)
    print("SAGE SPORTS PORTFOLIO DIVERSITY RECEIPT GENERATION")
    print("=" * 70)

    snapshots = make_market_universe()
    engine = DailySportsPortfolioEngine(target=50, parlay_share=0.30)
    portfolio = engine.build(snapshots, cycle_id="sports-diversity-audit-2026")

    sport_by_event = {s.event_id: s.sport for s in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event)

    # Validate eight metrics across overall portfolio
    assert report.total_records == 50, f"Expected 50 total records, got {report.total_records}"
    assert report.unique_events == 18, f"Expected 18 unique events, got {report.unique_events}"
    assert report.unique_sports == 4, f"Expected 4 unique sports, got {report.unique_sports}"
    assert report.unique_market_types == 4, f"Expected 4 market types (3 single + parlay), got {report.unique_market_types}"
    assert report.unique_event_market_types == 19, f"Expected 19 event market types, got {report.unique_event_market_types}"
    assert report.unique_event_market_lines == 19, f"Expected 19 event market lines, got {report.unique_event_market_lines}"
    assert report.unique_prediction_ids == 50, f"Expected 50 unique prediction IDs, got {report.unique_prediction_ids}"
    assert report.single_count == 35, f"Expected 35 single predictions, got {report.single_count}"
    assert report.parlay_count == 15, f"Expected 15 parlay predictions, got {report.parlay_count}"

    # Single-only diversity assertions (distinguishing singles from parlays)
    assert report.single_unique_events == 18, f"Expected 18 single unique events, got {report.single_unique_events}"
    assert report.single_unique_sports == 4, f"Expected 4 single unique sports, got {report.single_unique_sports}"
    assert report.single_unique_market_types == 3, f"Expected 3 single market types, got {report.single_unique_market_types}"
    assert report.single_unique_event_market_types == 18, f"Expected 18 single event market types, got {report.single_unique_event_market_types}"
    assert report.single_unique_event_market_lines == 18, f"Expected 18 single event market lines, got {report.single_unique_event_market_lines}"
    assert report.single_unique_prediction_ids == 35, f"Expected 35 single prediction IDs, got {report.single_unique_prediction_ids}"

    receipt_json = render_receipt(report)

    p1 = repo_root / "evidence_capture" / "sports_portfolio_diversity_receipt.json"
    p2 = repo_root / "portfolio_diversity_receipt.json"

    p1.parent.mkdir(parents=True, exist_ok=True)
    p1.write_text(receipt_json + "\n", encoding="utf-8")
    p2.write_text(receipt_json + "\n", encoding="utf-8")

    print("[✓] Eight Core Metrics & Single-Only Diversity Inspected & Verified:")
    print(json.dumps(report.to_dict(), indent=2))
    print(f"\n[✓] Receipt written to {p1}")
    print(f"[✓] Receipt written to {p2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
