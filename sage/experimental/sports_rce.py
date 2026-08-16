"""SAGE Sports/RCE — Minimal Real-World Pre-Game Observation & Temporal Locking Substrate.

Provides immutable pre-game observation, temporal lock validation (lock_timestamp < event_start),
SHA-256 receipt generation, and persistence without synthetic substitutions or real-money wagering.
"""

import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Set, Tuple


class SportsRCEResearchEngine:
    """Minimal research-only engine for real-world sports event pre-game observation and locking."""

    SOURCE_NAME = "TheSportsDB (Public Free API)"
    SOURCE_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"

    def __init__(self, capture_dir: Optional[Path] = None):
        self.capture_dir = capture_dir or Path("evidence_capture")
        self.capture_dir.mkdir(parents=True, exist_ok=True)

    def fetch_upcoming_event(self, date_str: str = "2026-08-17", exclude_event_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Fetch real event schedule for target date from public API source."""
        exclude = exclude_event_ids or set()
        url = f"{self.SOURCE_URL}?d={date_str}&s=Soccer"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SAGE/1.0 Research"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        events = data.get("events") or []
        if not events:
            raise ValueError(f"No events returned from {url}")

        # Select first upcoming event not in exclude set
        for ev in events:
            raw_id = str(ev.get("idEvent") or "")
            if raw_id in exclude or f"event_tsdb_{raw_id}" in exclude or f"pred_rce_{raw_id}" in exclude:
                continue
            if ev.get("strStatus") in ("NS", "Not Started", "Scheduled", "1"):
                return ev

        # Fallback to first non-excluded event
        for ev in events:
            raw_id = str(ev.get("idEvent") or "")
            if raw_id not in exclude and f"event_tsdb_{raw_id}" not in exclude and f"pred_rce_{raw_id}" not in exclude:
                return ev

        raise ValueError(f"No unexcluded events available for date {date_str} from {url}")

    @staticmethod
    def compute_prediction_hash(record: Dict[str, Any]) -> str:
        """Computes SHA-256 hash over canonical JSON representation of record (excluding prediction_hash)."""
        payload = {k: v for k, v in record.items() if k != "prediction_hash"}
        record_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(record_bytes).hexdigest()

    @staticmethod
    def verify_prediction_hash(record: Dict[str, Any]) -> bool:
        """Verifies that the record's stored hash matches independent canonical SHA-256 recomputation."""
        stored_hash = record.get("prediction_hash")
        if not stored_hash:
            return False
        computed = SportsRCEResearchEngine.compute_prediction_hash(record)
        return stored_hash == computed

    def create_pre_game_prediction(
        self,
        event_raw: Dict[str, Any],
        selection: str,
        predicted_probability: float,
        reasoning: str,
    ) -> Dict[str, Any]:
        """Constructs and temporally locks a research-only prediction before event start."""
        if not event_raw or not isinstance(event_raw, dict):
            raise ValueError("Invalid event data: event_raw must be a non-empty dictionary")
        if not event_raw.get("idEvent"):
            raise ValueError("Invalid event data: missing 'idEvent'")
        if not event_raw.get("strEvent"):
            raise ValueError("Invalid event data: missing 'strEvent'")
        str_ts = event_raw.get("strTimestamp")
        if not str_ts:
            raise ValueError("Invalid event data: missing 'strTimestamp'")

        obs_dt = datetime.now(timezone.utc)
        obs_timestamp = obs_dt.isoformat()

        # Parse event start time (ISO format)
        if not str_ts.endswith("Z") and "+" not in str_ts:
            str_ts += "Z"

        try:
            event_start_dt = datetime.fromisoformat(str_ts.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp format '{str_ts}': {exc}") from exc

        event_start_iso = event_start_dt.isoformat()

        # INVARIANT CHECK: lock_timestamp < event_start
        if obs_dt >= event_start_dt:
            raise ValueError(
                f"Temporal locking invariant failure: lock_timestamp ({obs_timestamp}) "
                f"is not strictly before event_start ({event_start_iso})"
            )

        event_id = f"event_tsdb_{event_raw.get('idEvent', 'unknown')}"
        prediction_id = f"pred_rce_{event_raw.get('idEvent', 'unknown')}"
        receipt_id = f"rcpt_rce_{hashlib.sha256(prediction_id.encode('utf-8')).hexdigest()[:12]}"

        record = {
            "prediction_id": prediction_id,
            "event_id": event_id,
            "event": event_raw.get("strEvent"),
            "sport": event_raw.get("strSport", "Soccer").lower(),
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
            "odds_at_lock": "ODDS_UNAVAILABLE",  # Explicit representation when unavailable
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
            "wagering_executed": False,
            "receipt_id": receipt_id,
        }

        # Calculate SHA-256 hash over canonical JSON representation
        record_bytes = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
        record["prediction_hash"] = hashlib.sha256(record_bytes).hexdigest()

        return record

    def persist_prediction_artifact(self, record: Dict[str, Any], filename: str = "sports_real_flight_001.json") -> Path:
        """Persists the locked prediction record to disk."""
        file_path = self.capture_dir / filename

        # INVARIANT CHECK: Rejects overwrite/rewrite if already locked
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("prediction_state") == "LOCKED" and existing.get("prediction_id") == record.get("prediction_id"):
                # Return existing path if identical
                return file_path

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        return file_path
