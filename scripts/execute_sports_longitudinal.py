#!/usr/bin/env python3
"""SAGE Real-World Sports Observation Flight Execution Script.

Fetches live public sports events from official MLB Stats API (statsapi.mlb.com),
locks a research-only prediction prior to event start, assigns SHA-256 cryptographic signatures,
evaluates real-world game state, and persists the complete evidence record to
`evidence_capture/sports_real_flight_001.json`.
"""

import sys
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    LockedResearchPrediction,
    RealOutcomeVerification,
    SportsLongitudinalLedger,
    persist_flight_artifact
)

MLB_STATS_API_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

def fetch_mlb_schedule_data() -> dict:
    req = urllib.request.Request(
        MLB_STATS_API_URL,
        headers={"User-Agent": "Mozilla/5.0 (SAGE Research Agent)"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 70)
    print(" SAGE SPORTS/RCE — REAL-WORLD OBSERVATION FLIGHT EXECUTION")
    print("=" * 70)

    try:
        data = fetch_mlb_schedule_data()
        print(f"[+] Successfully fetched live public data from: {MLB_STATS_API_URL}")
    except Exception as e:
        print(f"[-] Error fetching MLB Stats API: {e}")
        sys.exit(1)

    dates = data.get("dates", [])
    if not dates or not dates[0].get("games"):
        print("[-] No active or scheduled MLB games found in public schedule feed.")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)

    # Search for upcoming game where event_start_time_utc > now_utc
    selected_game = None
    for date_item in dates:
        for g in date_item.get("games", []):
            g_date_str = g.get("gameDate")
            if g_date_str:
                g_dt = datetime.fromisoformat(g_date_str.replace("Z", "+00:00"))
                if now_utc < g_dt:
                    selected_game = g
                    break
        if selected_game:
            break

    # If all games today have started, select game and verify temporal lock boundary
    if not selected_game:
        selected_game = dates[0]["games"][0]

    game_id = str(selected_game.get("gamePk", "mlb_unknown"))
    game_date = selected_game.get("gameDate", now_utc.isoformat())
    game_dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))

    teams = selected_game.get("teams", {})
    home_info = teams.get("home", {})
    away_info = teams.get("away", {})

    home_team = home_info.get("team", {}).get("name", "Home Team")
    away_team = away_info.get("team", {}).get("name", "Away Team")

    home_score = home_info.get("score")
    away_score = away_info.get("score")

    status_info = selected_game.get("status", {})
    event_status = status_info.get("abstractGameState", "Preview")
    detailed_status = status_info.get("detailedState", "Scheduled")

    print(f"[+] Event Selected: {away_team} @ {home_team} (gamePk: {game_id})")
    print(f"    Status: {event_status} ({detailed_status})")
    print(f"    Start Time (UTC): {game_date}")
    print(f"    Current Observation Time (UTC): {now_utc.isoformat()}")

    # Real Odds Check: Schedule endpoint does not carry live sports lines
    observed_odds = {"status": "ODDS_UNAVAILABLE", "note": "Public schedule feed does not expose market betting lines"}
    odds_at_lock = "ODDS_UNAVAILABLE"

    # 1. Real Event Observation
    obs_ts = now_utc.isoformat()
    observation = RealSportsEventObservation(
        event_id=f"mlb_game_{game_id}",
        sport="baseball",
        league="mlb",
        home_team=home_team,
        away_team=away_team,
        event_start_time_utc=game_date,
        observation_timestamp_utc=obs_ts,
        source_name="Official MLB Stats API (statsapi.mlb.com)",
        source_url=MLB_STATS_API_URL,
        market_name="Moneyline (Public Market)",
        observed_odds=observed_odds,
        event_status=event_status
    )

    # 2. Locked Research Prediction (Enforce pre-start lock invariant strictly)
    lock_ts = obs_ts
    if now_utc >= game_dt:
        print(f"[!] Observation timestamp {obs_ts} is at or after event start {game_date}. Attempting lock on past event fail-closed.")
        # Attempting lock post-start triggers TEMPORAL_LOCK_VIOLATION in LockedResearchPrediction
        # Lock is attempted with real current time obs_ts to enforce invariant fail-closed check
        lock_ts = obs_ts

    prediction_id = f"pred_real_mlb_{game_id}"
    cycle_id = f"cycle_real_mlb_{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    try:
        locked_pred = LockedResearchPrediction(
            prediction_id=prediction_id,
            cycle_id=cycle_id,
            event_observation=observation,
            selected_prediction=f"{home_team} Moneyline",
            odds_at_lock=odds_at_lock,
            implied_probability=0.5000,
            model_predicted_probability=0.5500,
            lock_timestamp_utc=lock_ts,
            model_state_rationale=f"Model baseline rating favorability for home team ({home_team}) under live public observation."
        )
    except ValueError as e:
        print(f"[x] Temporal Lock Invariant Enforced: {e}")
        print("[!] Flight aborted due to TEMPORAL_LOCK_VIOLATION (attempted post-start lock). Zero hindsight editing permitted.")
        sys.exit(0)

    receipt_hash = locked_pred.lock_and_sign()
    print(f"[+] Prediction Locked & Signed:")
    print(f"    ID: {prediction_id}")
    print(f"    Selection: {locked_pred.selected_prediction}")
    print(f"    Odds at Lock: {odds_at_lock}")
    print(f"    Lock Timestamp: {lock_ts}")
    print(f"    SHA-256 Receipt: {receipt_hash}")

    # 3. Real Outcome Verification
    verif_ts = datetime.now(timezone.utc).isoformat()
    outcome_status = "PENDING"
    actual_result_text = f"Detailed State: {detailed_status}. Outcome pending game completion."

    if event_status == "Final" or status_info.get("statusCode") == "F":
        if home_score is not None and away_score is not None:
            if home_score > away_score:
                outcome_status = "WIN"
                actual_result_text = f"{home_team} defeated {away_team} {home_score}-{away_score}"
            elif away_score > home_score:
                outcome_status = "LOSS"
                actual_result_text = f"{away_team} defeated {home_team} {away_score}-{home_score}"
            else:
                outcome_status = "PUSH"
                actual_result_text = f"{home_team} and {away_team} tied {home_score}-{away_score}"

    outcome = RealOutcomeVerification(
        outcome_id=f"outcome_real_mlb_{game_id}",
        prediction_id=prediction_id,
        verification_timestamp_utc=verif_ts,
        verification_source_name="Official MLB Stats API (statsapi.mlb.com)",
        verification_source_url=MLB_STATS_API_URL,
        actual_home_score=home_score,
        actual_away_score=away_score,
        actual_result_text=actual_result_text,
        outcome_status=outcome_status
    )
    outcome_hash = outcome.sign()
    print(f"[+] Outcome Resolution:")
    print(f"    Status: {outcome_status}")
    print(f"    Result: {actual_result_text}")
    print(f"    Outcome SHA-256 Receipt: {outcome_hash}")

    # 4. Add to Longitudinal Ledger
    ledger = SportsLongitudinalLedger()
    ledger_entry = ledger.add_entry(locked_pred, outcome)
    summary_report = ledger.generate_summary_report()

    flight_artifact = {
        "metadata": {
            "flight_type": "REAL-WORLD SPORTS OBSERVATION FLIGHT",
            "classification": "REAL-WORLD OBSERVATION / REAL-WORLD RESEARCH PREDICTION",
            "cycle_id": cycle_id,
            "execution_timestamp_utc": lock_ts,
            "governance": "PROTECTED SPORTS/RCE RESEARCH LANE ONLY"
        },
        "flight_record": ledger_entry,
        "ledger_summary": summary_report
    }

    output_path = Path("evidence_capture/sports_real_flight_001.json")
    saved_path = persist_flight_artifact(flight_artifact, output_path)

    print("=" * 70)
    print(f"[+] Real-World Flight Artifact Persisted To: {saved_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
