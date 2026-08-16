"""SAGE Sports/RCE — Minimal Real-World Pre-Game Observation & Temporal Locking Substrate.

Provides immutable pre-game observation, temporal lock validation (lock_timestamp < event_start),
SHA-256 receipt generation, and persistence without synthetic substitutions or real-money wagering.
"""

import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


def compute_prediction_hash(record: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash over canonical JSON representation excluding prediction_hash itself."""
    payload = {k: v for k, v in record.items() if k != "prediction_hash"}
    record_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(record_bytes).hexdigest()


class SportsRCEResearchEngine:
    """Minimal research-only engine for real-world sports event pre-game observation and locking."""

    SOURCE_NAME = "TheSportsDB (Public Free API)"
    SOURCE_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"

    def __init__(self, capture_dir: Optional[Path] = None):
        self.capture_dir = capture_dir or Path("evidence_capture")
        self.capture_dir.mkdir(parents=True, exist_ok=True)

    def fetch_upcoming_event(self, date_str: str = "2026-08-17") -> Dict[str, Any]:
        """Fetch real event schedule for target date from public API source."""
        url = f"{self.SOURCE_URL}?d={date_str}&s=Soccer"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SAGE/1.0 Research"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        events = data.get("events") or []
        if not events:
            raise ValueError(f"No events returned from {url}")

        for ev in events:
            if ev.get("strStatus") in ("NS", "Not Started", "Scheduled", "1"):
                return ev

        return events[0]

    def create_pre_game_prediction(
        self,
        event_raw: Dict[str, Any],
        selection: str,
        predicted_probability: float,
        reasoning: str,
    ) -> Dict[str, Any]:
        """Constructs and temporally locks a research-only prediction before event start."""
        obs_dt = datetime.now(timezone.utc)
        obs_timestamp = obs_dt.isoformat()

        # Strict non-fallback event timestamp parsing
        str_ts = event_raw.get("strTimestamp")
        if not str_ts:
            raise ValueError("Event source data missing required 'strTimestamp' field.")

        if not str_ts.endswith("Z") and "+" not in str_ts:
            str_ts += "Z"

        try:
            event_start_dt = datetime.fromisoformat(str_ts.replace("Z", "+00:00"))
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid event timestamp format in source data '{str_ts}': {err}")

        event_start_iso = event_start_dt.isoformat()

        # INVARIANT CHECK: lock_timestamp < event_start
        if obs_dt >= event_start_dt:
            raise ValueError(
                f"Temporal locking invariant failure: lock_timestamp ({obs_timestamp}) "
                f"is not strictly before event_start ({event_start_iso})"
            )

        event_id_raw = event_raw.get("idEvent")
        if not event_id_raw:
            raise ValueError("Event source data missing required 'idEvent' field.")

        event_id = f"event_tsdb_{event_id_raw}"
        prediction_id = f"pred_rce_{event_id_raw}"
        receipt_id = f"rcpt_rce_{hashlib.sha256(prediction_id.encode('utf-8')).hexdigest()[:12]}"

        record = {
            "prediction_id": prediction_id,
            "event_id": event_id,
            "event": event_raw.get("strEvent"),
            "sport": (event_raw.get("strSport") or "Soccer").lower(),
            "league": event_raw.get("strLeague"),
            "teams": {
                "home": event_raw.get("strHomeTeam"),
                "away": event_raw.get("strAwayTeam"),
            },
            "event_start": event_start_iso,
            "observation_timestamp": obs_timestamp,
            "prediction_timestamp": obs_timestamp,
            "market": "match_winner",
            "selection": selection,
            "odds_at_lock": "ODDS_UNAVAILABLE",
            "implied_probability": "ODDS_UNAVAILABLE",
            "predicted_probability": round(predicted_probability, 4),
            "confidence": round(predicted_probability, 4),
            "reasoning": reasoning,
            "source": self.SOURCE_NAME,
            "source_url": f"{self.SOURCE_URL}?d={event_raw.get('dateEvent', '2026-08-17')}&s=Soccer",
            "source_timestamp": obs_timestamp,
            "prediction_state": "LOCKED",
            "status": "PENDING",
            "classification": "REAL-WORLD RESEARCH PREDICTION",
            "evidence_status": {
                "real_observation_proven": True,
                "real_lock_proven": True,
                "real_odds_status": "ODDS_UNAVAILABLE",
                "model_input_type": "STATIC_RESEARCH_MODEL",
                "real_outcome_status": "PENDING_EVENT_COMPLETION",
            },
            "wagering_executed": False,
            "receipt_id": receipt_id,
        }

        record["prediction_hash"] = compute_prediction_hash(record)
        return record

    def persist_prediction_artifact(self, record: Dict[str, Any], filename: str = "sports_real_flight_001.json") -> Path:
        """Persists the locked prediction record to disk."""
        file_path = self.capture_dir / filename

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing = json.load(f)

            if existing.get("prediction_state") == "LOCKED":
                if existing.get("prediction_hash") == record.get("prediction_hash"):
                    return file_path
                raise ValueError(
                    f"Immutability Violation: Cannot overwrite existing locked artifact '{filename}' "
                    f"with a different prediction hash."
                )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        return file_path
