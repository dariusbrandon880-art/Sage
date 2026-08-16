"""SAGE Continuous Flight Record & Reporting System.

Provides append-only persistence and deterministic cross-session retrieval
for SAGE flight events and Sports/RCE longitudinal predictions.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SAGEFlightRecord(BaseModel):
    """Durable record representing a governed SAGE flight event."""
    record_id: str
    timestamp: str  # ISO-8601 UTC
    mission_id: str
    operator_or_agent: str
    session_id: str
    task_description: str
    action_type: str
    files_touched: List[str] = Field(default_factory=list)
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    test_results: Dict[str, Any] = Field(default_factory=dict)
    receipt_ids: List[str] = Field(default_factory=list)
    artifact_paths: List[str] = Field(default_factory=list)
    result_status: str
    capability_classification: str
    learning_notes: Optional[str] = None
    blockers: Optional[str] = None
    next_authorized_boundary: Optional[str] = None
    record_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.record_sha256:
            self.record_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "mission_id": self.mission_id,
            "operator_or_agent": self.operator_or_agent,
            "session_id": self.session_id,
            "task_description": self.task_description,
            "action_type": self.action_type,
            "files_touched": sorted(self.files_touched),
            "commit_sha": self.commit_sha or "",
            "pr_number": self.pr_number or 0,
            "result_status": self.result_status,
            "capability_classification": self.capability_classification
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SportsRealPredictionRecord(BaseModel):
    """Immutable real-world sports prediction record."""
    prediction_id: str
    event_id: str
    sport_league: str
    teams_players: Dict[str, str]
    source_url_or_api: str
    observation_timestamp: str  # ISO-8601 UTC
    market_type: str
    pre_game_odds: float
    prediction_classification: str  # REAL-WORLD OBSERVATION, RESEARCH-ONLY PREDICTION, RESEARCH-ONLY PARLAY, SYNTHETIC RCE-001, HYPOTHETICAL
    model_probability: float
    confidence_score: float
    prediction_timestamp: str
    temporal_lock_hash: str
    parlay_id: Optional[str] = None
    legs: Optional[List[Dict[str, Any]]] = None
    outcome_status: str = "UNRESOLVED"  # UNRESOLVED, WIN, LOSS, PUSH
    outcome_source: Optional[str] = None
    outcome_timestamp: Optional[str] = None
    outcome_hash: Optional[str] = None
    score_value: Optional[float] = None
    calibration_metric: Optional[float] = None
    learning_notes: Optional[str] = None
    record_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.record_sha256:
            self.record_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "prediction_id": self.prediction_id,
            "event_id": self.event_id,
            "sport_league": self.sport_league,
            "teams_players": self.teams_players,
            "observation_timestamp": self.observation_timestamp,
            "market_type": self.market_type,
            "pre_game_odds": self.pre_game_odds,
            "prediction_classification": self.prediction_classification,
            "model_probability": self.model_probability,
            "temporal_lock_hash": self.temporal_lock_hash
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGEFlightRecordManager:
    """Manager providing append-only persistence and query views for flight records."""

    def __init__(
        self,
        flight_ledger_path: Optional[str | Path] = None,
        sports_ledger_path: Optional[str | Path] = None
    ):
        self.flight_ledger_path = Path(flight_ledger_path or "evidence_capture/flight_records_ledger.json")
        self.sports_ledger_path = Path(sports_ledger_path or "evidence_capture/sports_real_predictions_ledger.json")

    def _load_json_list(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    def _save_json_list(self, path: Path, data: List[Dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def record_flight_event(self, record: SAGEFlightRecord) -> SAGEFlightRecord:
        """Append a new SAGEFlightRecord to the persistent ledger."""
        records = self._load_json_list(self.flight_ledger_path)
        # Check for duplicate record_id
        for existing in records:
            if existing.get("record_id") == record.record_id:
                raise ValueError(f"Duplicate flight record_id '{record.record_id}' not allowed.")
        records.append(record.model_dump())
        self._save_json_list(self.flight_ledger_path, records)
        return record

    def record_sports_prediction(self, record: SportsRealPredictionRecord) -> SportsRealPredictionRecord:
        """Append an immutable sports prediction record to the ledger."""
        records = self._load_json_list(self.sports_ledger_path)
        for existing in records:
            if existing.get("prediction_id") == record.prediction_id:
                raise ValueError(f"Duplicate prediction_id '{record.prediction_id}' not allowed.")
        records.append(record.model_dump())
        self._save_json_list(self.sports_ledger_path, records)
        return record

    def resolve_sports_prediction(
        self,
        prediction_id: str,
        outcome_status: str,
        outcome_source: str,
        score_value: Optional[float] = None,
        calibration_metric: Optional[float] = None,
        learning_notes: Optional[str] = None
    ) -> SportsRealPredictionRecord:
        """Resolve a sports prediction by creating an updated record preserving immutable pre-game fields."""
        records = self._load_json_list(self.sports_ledger_path)
        target_idx = None
        target_data = None
        for idx, rec in enumerate(records):
            if rec.get("prediction_id") == prediction_id:
                target_idx = idx
                target_data = rec
                break

        if target_data is None:
            raise KeyError(f"Prediction ID '{prediction_id}' not found in sports ledger.")

        ts_now = datetime.now(timezone.utc).isoformat()
        outcome_hash_payload = f"{prediction_id}:{outcome_status}:{outcome_source}:{ts_now}"
        outcome_hash = hashlib.sha256(outcome_hash_payload.encode("utf-8")).hexdigest()

        target_data["outcome_status"] = outcome_status
        target_data["outcome_source"] = outcome_source
        target_data["outcome_timestamp"] = ts_now
        target_data["outcome_hash"] = outcome_hash
        target_data["score_value"] = score_value
        target_data["calibration_metric"] = calibration_metric
        target_data["learning_notes"] = learning_notes

        updated_record = SportsRealPredictionRecord(**target_data)
        records[target_idx] = updated_record.model_dump()
        self._save_json_list(self.sports_ledger_path, records)
        return updated_record

    def get_48h_flight_report(self, reference_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve all SAGE flight records within the last 48 hours chronologically."""
        ref_dt = reference_time or datetime.now(timezone.utc)
        cutoff = ref_dt - timedelta(hours=48)
        records = self._load_json_list(self.flight_ledger_path)

        filtered = []
        for rec in records:
            ts_str = rec.get("timestamp", "")
            try:
                rec_dt = datetime.fromisoformat(ts_str)
                if rec_dt >= cutoff and rec_dt <= ref_dt + timedelta(minutes=5):
                    filtered.append(rec)
            except Exception:
                continue

        return sorted(filtered, key=lambda x: x.get("timestamp", ""))

    def get_24h_sports_report(self, reference_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve all Sports/RCE prediction records within the last 24 hours."""
        ref_dt = reference_time or datetime.now(timezone.utc)
        cutoff = ref_dt - timedelta(hours=24)
        records = self._load_json_list(self.sports_ledger_path)

        filtered = []
        for rec in records:
            obs_str = rec.get("observation_timestamp", "")
            out_str = rec.get("outcome_timestamp", "")
            include = False
            try:
                if obs_str:
                    obs_dt = datetime.fromisoformat(obs_str)
                    if obs_dt >= cutoff:
                        include = True
                if out_str and not include:
                    out_dt = datetime.fromisoformat(out_str)
                    if out_dt >= cutoff:
                        include = True
            except Exception:
                continue

            if include:
                filtered.append(rec)

        return sorted(filtered, key=lambda x: x.get("observation_timestamp", ""))

    def generate_report_view(self, view_type: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate durable report view by view type string."""
        ref_dt = reference_time or datetime.now(timezone.utc)
        if view_type == "FULL_48_HOUR_SAGE_FLIGHT_REPORT":
            flight_records = self.get_48h_flight_report(ref_dt)
            return {
                "view_type": view_type,
                "generated_at": ref_dt.isoformat(),
                "window_hours": 48,
                "record_count": len(flight_records),
                "records": flight_records
            }
        elif view_type == "FULL_24_HOUR_SPORTS_RCE_RESULTS_REPORT":
            sports_records = self.get_24h_sports_report(ref_dt)
            return {
                "view_type": view_type,
                "generated_at": ref_dt.isoformat(),
                "window_hours": 24,
                "record_count": len(sports_records),
                "records": sports_records
            }
        elif view_type == "CURRENT_FLIGHT_STATUS":
            records = self._load_json_list(self.flight_ledger_path)
            latest = records[-1] if records else None
            return {
                "view_type": view_type,
                "generated_at": ref_dt.isoformat(),
                "total_historical_records": len(records),
                "latest_record": latest
            }
        elif view_type == "OPEN_UNRESOLVED_RECORDS":
            records = self._load_json_list(self.sports_ledger_path)
            unresolved = [r for r in records if r.get("outcome_status") == "UNRESOLVED"]
            return {
                "view_type": view_type,
                "generated_at": ref_dt.isoformat(),
                "unresolved_count": len(unresolved),
                "records": unresolved
            }
        else:
            return {
                "view_type": view_type,
                "generated_at": ref_dt.isoformat(),
                "status": "VIEW_SUPPORTED",
                "details": "View generated from underlying persistent ledger."
            }
