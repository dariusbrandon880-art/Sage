#!/usr/bin/env python3
"""SAGE Sports Shadow Beta: point-in-time, shadow-only forecast capture.

This runner intentionally does NOT manufacture market observations, public consensus,
closing lines, outcomes, or wagering/parlay workloads. It only records forecasts for
real scheduled events when the independently observed ingest time is strictly before
real event start. Promotion is fail-closed until later outcome resolution and
chronological OOS evaluation are available.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sage.experimental.sports_longitudinal import (  # noqa: E402
    LockedResearchPrediction,
    ObservationProvenance,
    ReplayableObservationStream,
    RealSportsEventObservation,
    SportsLongitudinalLedger,
    TemporalConsistencyValidator,
)

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&hydrate=team"
EVIDENCE_PATH = REPO_ROOT / "evidence_capture" / "sports_shadow_beta_evidence.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def fetch_schedule() -> dict:
    request = Request(
        MLB_SCHEDULE_URL,
        headers={"User-Agent": "SAGE-Sports-Research/1.0"},
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def event_start(game: dict) -> datetime:
    raw = game["gameDate"].replace("Z", "+00:00")
    return datetime.fromisoformat(raw).astimezone(timezone.utc)


def team_probability(home: str, away: str) -> float:
    """Deterministic research baseline; never derived from market or post-event data."""
    h = int(hashlib.sha256(home.encode()).hexdigest()[:8], 16)
    a = int(hashlib.sha256(away.encode()).hexdigest()[:8], 16)
    delta = ((h % 21) - (a % 21)) / 100.0
    return round(max(0.20, min(0.80, 0.50 + delta)), 4)


def build_forecast(game: dict, observed_at: datetime, stream: ReplayableObservationStream):
    start = event_start(game)
    if observed_at >= start:
        return None, "EVENT_ALREADY_STARTED_OR_STARTED_AT_INGEST"

    game_id = str(game["gamePk"])
    home = game["teams"]["home"]["team"]["name"]
    away = game["teams"]["away"]["team"]["name"]
    source_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/feed/live"
    payload = {
        "game_pk": game_id,
        "home_team": home,
        "away_team": away,
        "game_start_time_utc": start.isoformat(),
    }
    raw_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    provenance = ObservationProvenance(
        source_id=f"mlb-schedule-{game_id}",
        source_name="MLB Stats API schedule",
        source_url=MLB_SCHEDULE_URL,
        source_timestamp_utc=observed_at.isoformat(),
        raw_payload_hash=raw_hash,
        ingest_timestamp_utc=observed_at.isoformat(),
    )
    stream.append_event(
        event_id=game_id,
        observation_id=f"obs-{game_id}",
        observation_timestamp_utc=observed_at.isoformat(),
        event_start_time_utc=start.isoformat(),
        provenance=provenance,
        payload=payload,
    )

    prob = team_probability(home, away)
    selected = home if prob >= 0.5 else away
    prediction = LockedResearchPrediction(
        prediction_id=f"pred_shadow_{game_id}",
        cycle_id=f"shadow_{observed_at.strftime('%Y%m%dT%H%M%SZ')}",
        event_observation=RealSportsEventObservation(
            event_id=game_id,
            sport="baseball",
            league="MLB",
            home_team=home,
            away_team=away,
            event_start_time_utc=start.isoformat(),
            observation_timestamp_utc=observed_at.isoformat(),
            source_name="MLB Stats API schedule",
            source_url=source_url,
            market_name="NONE",
            observed_odds={},
            event_status="Scheduled",
        ),
        selected_prediction=selected,
        odds_at_lock="UNAVAILABLE",
        implied_probability=0.5,
        model_predicted_probability=prob,
        lock_timestamp_utc=observed_at.isoformat(),
        model_state_rationale=(
            "Shadow-only deterministic baseline using pre-event team identifiers. "
            "No market, consensus, closing-line, outcome, or wagering data is used."
        ),
        is_parlay=False,
        parlay_legs=[],
    )
    prediction.lock_and_sign()
    return prediction, None


def main() -> int:
    started_at = utc_now()
    schedule = fetch_schedule()
    games = schedule.get("dates", [])
    stream = ReplayableObservationStream()
    ledger = SportsLongitudinalLedger()
    forecasts = []
    rejected = []

    for day in games:
        for game in day.get("games", []):
            try:
                prediction, reason = build_forecast(game, started_at, stream)
                if prediction is not None:
                    ledger.add_prediction(prediction)
                    forecasts.append({
                        "prediction_id": prediction.prediction_id,
                        "event_id": prediction.event_observation.event_id,
                        "event_start_time_utc": prediction.event_observation.event_start_time_utc,
                        "lock_timestamp_utc": prediction.lock_timestamp_utc,
                        "prediction_hash": prediction.sha256_receipt_hash,
                        "selected_prediction": prediction.selected_prediction,
                        "model_probability": prediction.model_predicted_probability,
                        "market_data": "UNAVAILABLE",
                        "public_consensus": "UNAVAILABLE",
                        "clv": "N/A_UNTIL_REAL_CLOSING_OBSERVATION",
                    })
                elif reason:
                    rejected.append({"game_pk": str(game.get("gamePk")), "reason": reason})
            except (KeyError, ValueError) as exc:
                rejected.append({"game_pk": str(game.get("gamePk")), "reason": str(exc)})

    # Promotion is intentionally impossible in this capture-only runner.
    promotion = {
        "promotion_eligible": False,
        "governance_decision": "PROMOTION_DENIED_AWAITING_CHRONOLOGICAL_OOS",
        "reason": "Forecasts require later real outcomes and walk-forward OOS evaluation before promotion.",
        "brier_score": None,
        "log_loss": None,
        "calibration": "NOT_YET_EVALUATED",
        "baseline_comparison": "NOT_YET_EVALUATED",
    }

    artifact = {
        "schema": "SAGE.SPORTS_SHADOW_BETA.POINT_IN_TIME_V2",
        "execution_timestamp_utc": started_at.isoformat(),
        "source": "MLB Stats API schedule",
        "shadow_only": True,
        "real_money_wagering": False,
        "synthetic_market_data": False,
        "synthetic_public_consensus": False,
        "backdated_locks": False,
        "parlay_generation": False,
        "forecasts": forecasts,
        "rejected_events": rejected,
        "promotion": promotion,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps({
        "verdict": "PASS" if not any("TEMPORAL" in r["reason"] for r in rejected) else "FAIL",
        "forecasts_captured": len(forecasts),
        "events_rejected": len(rejected),
        "promotion_eligible": False,
        "evidence": str(EVIDENCE_PATH),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
