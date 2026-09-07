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
    parser.add_argument("--target", type=int, default=50, help="Target daily portfolio size (default: 50)")
    parser.add_argument("--parlay-share", type=float, default=0.30, help="Target parlay share ratio (default: 0.30)")
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
        default_multi_fixture = repo_root / "tests" / "fixtures" / "sports_real_multi_sport_feed_response.json"
        default_legacy_fixture = repo_root / "tests" / "fixtures" / "sports_real_feed_response.json"
        if args.fixture_path:
            fixture_file = Path(args.fixture_path)
        else:
            fixture_file = default_multi_fixture if default_multi_fixture.exists() else default_legacy_fixture
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

    # Build predictions and portfolio audit
    target = args.target
    try:
        engine = DailySportsPortfolioEngine(target=target, parlay_share=args.parlay_share)
        portfolio = engine.build(snapshots, cycle_id="sports-feed-probe-2026")
    except ValueError as err:
        if "DAILY_TARGET_UNMET" in str(err):
            achievable_target = min(len(snapshots), target)
            if achievable_target >= 1:
                print(f"[!] Requested target {target} unmet for snapshot count ({len(snapshots)} snapshots); adapting target to {achievable_target}")
                engine = DailySportsPortfolioEngine(target=achievable_target, parlay_share=args.parlay_share)
                portfolio = engine.build(snapshots, cycle_id="sports-feed-probe-2026")
            else:
                raise
        else:
            raise
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
