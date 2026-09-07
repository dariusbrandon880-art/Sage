#!/usr/bin/env python3
"""Governed Live Probe / External Feed Flight Script for SAGE Sports Quantitative Substrate.

Provides governed, read-only probing of live sports market feeds or deterministic fallback
to recorded real-world fixtures. Never authenticates or executes wagers (wagering_executed = False).

Usage:
    # Deterministic fixture mode (default)
    python scripts/probe_live_sports_feed.py

    # Opt-in live probe mode (with API key)
    python scripts/probe_live_sports_feed.py --live --api-key YOUR_ODDS_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from datetime import datetime, timezone

from sage.experimental.sports_longitudinal import (  # noqa: E402
    SportsLongitudinalLedger,
    ingest_portfolio_into_ledger,
)
from sage.experimental.sports_quant import (  # noqa: E402
    DailySportsPortfolioEngine,
    MarketProvenance,
    ProvenanceClass,
    RealMarketFeedAdapter,
)
from sage.experimental.sports_quant.portfolio_audit import (  # noqa: E402
    build_diversity_report,
    render_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="SAGE Sports Live Feed Probe & Provenance Flight")
    parser.add_argument("--live", action="store_true", help="Opt-in to fetch live feed from external HTTP endpoint")
    parser.add_argument("--endpoint", type=str, default="https://api.the-odds-api.com/v4/sports/upcoming/odds", help="External market odds API endpoint")
    parser.add_argument("--api-key", type=str, default=None, help="API key for external odds provider (or SAGE_SPORTS_API_KEY / ODDS_API_KEY env)")
    parser.add_argument("--fixture-path", type=str, default=None, help="Custom fixture JSON file path")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("SAGE_SPORTS_API_KEY") or os.environ.get("ODDS_API_KEY")
    live_mode = args.live or (api_key is not None and "--fixture-path" not in sys.argv)

    print("=" * 70)
    print("SAGE SPORTS EXTERNAL MARKET FEED PROBE")
    print("=" * 70)

    if live_mode and api_key:
        print(f"[!] LIVE PROBE MODE ENABLED: fetching from {args.endpoint}")
        try:
            snapshots, provenance = RealMarketFeedAdapter.fetch_live_feed(
                endpoint=args.endpoint,
                api_key=api_key,
                provider="The Odds API",
            )
        except Exception as e:
            print(f"[X] Live fetch failed: {e}")
            print("[X] Live probe aborted; no fixture fallback is recorded as live evidence")
            return 1

    if not live_mode:
        fixture_file = Path(args.fixture_path) if args.fixture_path else repo_root / "tests" / "fixtures" / "sports_real_feed_response.json"
        print(f"[i] FIXTURE MODE: loading captured real-feed payload from {fixture_file}")
        if not fixture_file.exists():
            print(f"[X] Error: Fixture file not found at {fixture_file}")
            return 1
        raw_text = fixture_file.read_text(encoding="utf-8")
        snapshots, provenance = RealMarketFeedAdapter.parse_raw_feed(
            raw_payload=raw_text,
            provider="FanDuel / Odds API Fixture",
            endpoint=str(fixture_file),
            provenance_class=ProvenanceClass.FIXTURE.value,
        )

    print(f"[✓] Market Ingestion Complete: {len(snapshots)} snapshots across {len(provenance.event_ids)} events")
    print(f"[✓] Provenance Class: {provenance.provenance_class}")
    print(f"[✓] Raw Payload SHA-256: {provenance.raw_payload_hash}")
    print(f"[✓] Normalized Payload SHA-256: {provenance.normalized_payload_hash}")

    # Build 50-record prediction portfolio
    cycle_id = f"sports-feed-probe-50-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    engine = DailySportsPortfolioEngine(target=50, parlay_share=0.30)
    try:
        portfolio = engine.build(snapshots, cycle_id=cycle_id)
    except Exception as e:
        print(f"[X] Portfolio construction failed: {e}")
        print("[X] Live probe aborted; failing closed without synthetic fallback")
        return 1

    print(f"[✓] 50-Record Portfolio Built: {len(portfolio.records)} records ({portfolio.single_count} singles, {portfolio.parlay_count} parlays)")

    # Ingest 50-record batch into canonical longitudinal ledger
    ledger_path = repo_root / "evidence_capture" / "sports_longitudinal_ledger.json"
    ledger = SportsLongitudinalLedger(storage_path=ledger_path)
    locked_preds = ingest_portfolio_into_ledger(
        portfolio_records=portfolio.records,
        snapshots=snapshots,
        ledger=ledger,
        cycle_id=cycle_id,
        provenance=provenance,
    )
    print(f"[✓] Persisted {len(locked_preds)} locked predictions into longitudinal ledger at {ledger_path}")

    # Build and write portfolio audit report receipt
    sport_by_event = {s.event_id: s.sport for s in snapshots}
    report = build_diversity_report(portfolio.records, sport_by_event, provenance=provenance)

    out_file = repo_root / "evidence_capture" / "sports_live_probe_receipt.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(render_receipt(report) + "\n", encoding="utf-8")

    print(f"\n[✓] Evidence receipt persisted to {out_file}")
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
