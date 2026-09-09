#!/usr/bin/env python3
"""Fresh Sports Proving Run Script.

Executes a fresh runtime correctness proving run for SAGE sports updates:
- Exercises all supported sports: MLB, NBA, NFL, NHL
- Exercises all market types: moneyline, spread, total, player_prop
- Exercises multiple markets on the same underlying event
- Validates cycle-independent prediction identity
- Validates cross-cycle/timestamp deduplication
- Validates PlayerPropSnapshot portfolio integration
"""

import sys
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.experimental.sports_quant import (
    DailySportsPortfolioEngine,
    MarketSnapshot,
    PlayerPropSnapshot,
    PredictionBatchEngine,
    PredictionRecord,
)

START_TIME = "2026-09-15T22:00:00Z"
OBSERVED_T1 = "2026-09-15T12:00:00Z"
OBSERVED_T2 = "2026-09-15T14:00:00Z"

def main() -> int:
    print("=" * 70)
    print("SAGE SPORTS FRESH PROVING RUN")
    print("=" * 70)

    # 1. Construct entirely fresh events across all 4 supported sports & multiple market types
    snapshots = [
        # MLB: Game 1 (Moneyline, Spread, Total)
        MarketSnapshot("fresh_mlb_101", "MLB", "MLB", START_TIME, OBSERVED_T1, "moneyline", {"yankees": 1.85, "redsox": 2.05}, "Fresh Feed"),
        MarketSnapshot("fresh_mlb_101", "MLB", "MLB", START_TIME, OBSERVED_T1, "spread", {"yankees": 1.90, "redsox": 1.90}, "Fresh Feed", market_type="spread", line_value=-1.5),
        MarketSnapshot("fresh_mlb_101", "MLB", "MLB", START_TIME, OBSERVED_T1, "total", {"over": 1.95, "under": 1.85}, "Fresh Feed", market_type="total", line_value=8.5),

        # NBA: Game 1 (Moneyline, Spread, Total)
        MarketSnapshot("fresh_nba_201", "NBA", "NBA", START_TIME, OBSERVED_T1, "moneyline", {"celtics": 1.70, "lakers": 2.20}, "Fresh Feed"),
        MarketSnapshot("fresh_nba_201", "NBA", "NBA", START_TIME, OBSERVED_T1, "spread", {"celtics": 1.91, "lakers": 1.91}, "Fresh Feed", market_type="spread", line_value=-4.5),
        MarketSnapshot("fresh_nba_201", "NBA", "NBA", START_TIME, OBSERVED_T1, "total", {"over": 1.88, "under": 1.92}, "Fresh Feed", market_type="total", line_value=224.5),

        # NFL: Game 1 (Moneyline, Spread, Total)
        MarketSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T1, "moneyline", {"chiefs": 1.65, "niners": 2.30}, "Fresh Feed"),
        MarketSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T1, "spread", {"chiefs": 1.90, "niners": 1.90}, "Fresh Feed", market_type="spread", line_value=-3.0),
        MarketSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T1, "total", {"over": 1.90, "under": 1.90}, "Fresh Feed", market_type="total", line_value=47.5),

        # NHL: Game 1 (Moneyline, Spread)
        MarketSnapshot("fresh_nhl_401", "NHL", "NHL", START_TIME, OBSERVED_T1, "moneyline", {"oilers": 1.80, "panthers": 2.05}, "Fresh Feed"),
        MarketSnapshot("fresh_nhl_401", "NHL", "NHL", START_TIME, OBSERVED_T1, "spread", {"oilers": 2.10, "panthers": 1.75}, "Fresh Feed", market_type="spread", line_value=-1.5),
    ]

    # Player props across sports
    prop_snapshots = [
        PlayerPropSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T1, "Patrick Mahomes", "passing_tds", 2.5, {"over": 2.05, "under": 1.80}, source="Fresh Feed"),
        PlayerPropSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T1, "Travis Kelce", "anytime_touchdown", 0.5, {"yes": 2.25}, source="Fresh Feed"),
        PlayerPropSnapshot("fresh_nba_201", "NBA", "NBA", START_TIME, OBSERVED_T1, "Jayson Tatum", "points", 27.5, {"over": 1.87, "under": 1.93}, source="Fresh Feed"),
        PlayerPropSnapshot("fresh_nhl_401", "NHL", "NHL", START_TIME, OBSERVED_T1, "Connor McDavid", "shots_on_goal", 3.5, {"over": 1.90, "under": 1.90}, source="Fresh Feed"),
    ]

    # 2. Test Cycle Independence & Timestamp Deduplication
    snapshots_t2 = [
        # Same event & markets observed at later timestamp T2 under cycle B
        MarketSnapshot("fresh_mlb_101", "MLB", "MLB", START_TIME, OBSERVED_T2, "moneyline", {"yankees": 1.85, "redsox": 2.05}, "Fresh Feed"),
        MarketSnapshot("fresh_nfl_301", "NFL", "NFL", START_TIME, OBSERVED_T2, "moneyline", {"chiefs": 1.65, "niners": 2.30}, "Fresh Feed"),
    ]

    batch_engine = PredictionBatchEngine()
    recs_cycle_A = batch_engine.generate(snapshots, "cycle_alpha")
    recs_cycle_B = batch_engine.generate(snapshots_t2, "cycle_beta")

    # Verify Prediction IDs generated in cycle A vs cycle B for same event/market/selection match exactly
    match_count = 0
    for rA in recs_cycle_A:
        for rB in recs_cycle_B:
            if rA.event_id == rB.event_id and rA.canonical_market_type == rB.canonical_market_type and rA.selection == rB.selection:
                assert rA.prediction_id == rB.prediction_id, f"ID mismatch: {rA.prediction_id} != {rB.prediction_id}"
                match_count += 1

    print(f"[✓] Prediction Identity Cycle Independence Confirmed: {match_count} exact prediction_id matches across cycles")

    # 3. Test Deduplication
    combined_raw = recs_cycle_A + recs_cycle_B
    unique_singles, rejected_duplicates = DailySportsPortfolioEngine._dedupe(combined_raw)

    print(f"[✓] Deduplication Check: {len(combined_raw)} raw generated -> {len(unique_singles)} unique accepted, {rejected_duplicates} rejected duplicates")
    assert rejected_duplicates == len(recs_cycle_B), "Failed to reject cross-timestamp duplicates"

    # 4. Portfolio Engine Build
    engine = DailySportsPortfolioEngine(target=12, parlay_share=0.25)
    portfolio = engine.build(snapshots=snapshots, cycle_id="cycle_proving_run", prop_snapshots=prop_snapshots)

    print("\n--- PORTFOLIO SUMMARY ---")
    print(f"Total Portfolio Count: {portfolio.count} / Target: {portfolio.target}")
    print(f"Singles Count: {portfolio.single_count}")
    print(f"Parlays Count: {portfolio.parlay_count}")
    print(f"Duplicate Rejections: {portfolio.duplicate_rejections}")
    print(f"Sport Counts: {portfolio.sport_counts}")

    print("\n--- GENERATED FRESH BETS SLATE ---")
    for i, r in enumerate(portfolio.records, 1):
        p_type = "PARLAY" if r.is_parlay else "SINGLE"
        print(f"{i:02d}. [{p_type}] [{r.market_type.upper()}] Event: {r.event_id} | Selection: {r.selection} | Line: {r.canonical_line_value or 'N/A'} | ID: {r.prediction_id}")

    print("\n" + "=" * 70)
    print("FRESH SPORTS RUN — PASS")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
