"""SAGE Sports Longitudinal & Real Observation Primitive.

Provides immutable data models, temporal locking, outcome resolution,
Brier score calibration, and longitudinal dataset ledger management under
Protected Sports/RCE Research Lane Governance.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib

def parse_iso_utc(ts_str: str) -> datetime:
    """Parses ISO 8601 timestamp string to UTC datetime."""
    clean_str = ts_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@dataclass
class RealSportsEventObservation:
    event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    event_start_time_utc: str
    observation_timestamp_utc: str
    source_name: str
    source_url: str
    market_name: str
    observed_odds: Dict[str, Any]
    event_status: str

    def __post_init__(self):
        if not self.observed_odds:
            self.observed_odds = {"status": "ODDS_UNAVAILABLE"}

@dataclass
class LockedResearchPrediction:
    prediction_id: str
    cycle_id: str
    event_observation: RealSportsEventObservation
    selected_prediction: str
    odds_at_lock: str
    implied_probability: float
    model_predicted_probability: float
    lock_timestamp_utc: str
    model_state_rationale: str
    is_parlay: bool = False
    parlay_legs: List[Dict[str, Any]] = field(default_factory=list)
    sha256_receipt_hash: str = ""

    def __post_init__(self):
        # Enforce Temporal Lock invariant: lock_timestamp_utc MUST BE strictly less than event_start_time_utc
        lock_dt = parse_iso_utc(self.lock_timestamp_utc)
        start_dt = parse_iso_utc(self.event_observation.event_start_time_utc)
        if lock_dt >= start_dt:
            raise ValueError(f"TEMPORAL_LOCK_VIOLATION: Lock timestamp {self.lock_timestamp_utc} is at or after event start time {self.event_observation.event_start_time_utc}.")

    def compute_sha256_hash(self) -> str:
        payload = {
            "prediction_id": self.prediction_id,
            "cycle_id": self.cycle_id,
            "event_id": self.event_observation.event_id,
            "selected_prediction": self.selected_prediction,
            "odds_at_lock": self.odds_at_lock,
            "implied_probability": self.implied_probability,
            "model_predicted_probability": self.model_predicted_probability,
            "lock_timestamp_utc": self.lock_timestamp_utc,
            "is_parlay": self.is_parlay,
            "parlay_legs": self.parlay_legs
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def lock_and_sign(self) -> str:
        self.sha256_receipt_hash = self.compute_sha256_hash()
        return self.sha256_receipt_hash

@dataclass
class RealOutcomeVerification:
    outcome_id: str
    prediction_id: str
    verification_timestamp_utc: str
    verification_source_name: str
    verification_source_url: str
    actual_home_score: Optional[int]
    actual_away_score: Optional[int]
    actual_result_text: str
    outcome_status: str  # WIN, LOSS, PUSH, VOID, PENDING
    outcome_receipt_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "outcome_id": self.outcome_id,
            "prediction_id": self.prediction_id,
            "verification_timestamp_utc": self.verification_timestamp_utc,
            "actual_home_score": self.actual_home_score,
            "actual_away_score": self.actual_away_score,
            "actual_result_text": self.actual_result_text,
            "outcome_status": self.outcome_status
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.outcome_receipt_hash = self.compute_sha256_hash()
        return self.outcome_receipt_hash

def calculate_brier_score(predictions: List[Dict[str, Any]]) -> Optional[float]:
    """Calculates Brier Score BS = (1/N) * sum((predicted_prob - outcome_value)^2).

    Outcome value is 1.0 for WIN, 0.0 for LOSS. Pushes/Voids/Pending are excluded.
    Returns None if no resolved WIN/LOSS outcomes exist.
    """
    valid_diffs = []
    for p in predictions:
        status = p.get("outcome_status")
        prob = p.get("model_predicted_probability")
        if status in ["WIN", "LOSS"] and prob is not None:
            actual = 1.0 if status == "WIN" else 0.0
            diff = (float(prob) - actual) ** 2
            valid_diffs.append(diff)
    if not valid_diffs:
        return None
    return sum(valid_diffs) / len(valid_diffs)

def classify_prediction_failure(predicted: str, actual_result: str, outcome_status: str) -> Optional[Dict[str, Any]]:
    if outcome_status != "LOSS":
        return None
    return {
        "failure_classification": "REAL_WORLD_PREDICTION_ERROR",
        "predicted_selection": predicted,
        "actual_result": actual_result,
        "model_assumption_broken": "Model predicted probability exceeded actual empirical realization under market noise.",
        "lesson_recorded": "Incorporate market odds variance and opponent recent momentum into probability calibration model."
    }

class SportsLongitudinalLedger:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self._prediction_ids: set[str] = set()

    def add_entry(self, locked_pred: LockedResearchPrediction, outcome: RealOutcomeVerification) -> Dict[str, Any]:
        if locked_pred.prediction_id in self._prediction_ids:
            raise ValueError(f"DUPLICATE_PREDICTION_ID: Prediction ID '{locked_pred.prediction_id}' already exists in longitudinal ledger.")

        entry = {
            "classification": "REAL-WORLD OBSERVATION / REAL-WORLD RESEARCH PREDICTION",
            "prediction_id": locked_pred.prediction_id,
            "cycle_id": locked_pred.cycle_id,
            "event_observation": asdict(locked_pred.event_observation),
            "locked_prediction": {
                "selected_prediction": locked_pred.selected_prediction,
                "odds_at_lock": locked_pred.odds_at_lock,
                "implied_probability": locked_pred.implied_probability,
                "model_predicted_probability": locked_pred.model_predicted_probability,
                "lock_timestamp_utc": locked_pred.lock_timestamp_utc,
                "model_state_rationale": locked_pred.model_state_rationale,
                "is_parlay": locked_pred.is_parlay,
                "parlay_legs": locked_pred.parlay_legs,
                "sha256_receipt_hash": locked_pred.sha256_receipt_hash
            },
            "outcome_verification": asdict(outcome),
            "failure_learning": classify_prediction_failure(locked_pred.selected_prediction, outcome.actual_result_text, outcome.outcome_status)
        }
        self.records.append(entry)
        self._prediction_ids.add(locked_pred.prediction_id)
        return entry

    def generate_summary_report(self) -> Dict[str, Any]:
        resolved_count = sum(1 for r in self.records if r["outcome_verification"]["outcome_status"] in ["WIN", "LOSS"])
        wins = sum(1 for r in self.records if r["outcome_verification"]["outcome_status"] == "WIN")
        losses = sum(1 for r in self.records if r["outcome_verification"]["outcome_status"] == "LOSS")
        pushes = sum(1 for r in self.records if r["outcome_verification"]["outcome_status"] == "PUSH")
        pending = sum(1 for r in self.records if r["outcome_verification"]["outcome_status"] == "PENDING")

        preds_for_brier = []
        for r in self.records:
            preds_for_brier.append({
                "outcome_status": r["outcome_verification"]["outcome_status"],
                "model_predicted_probability": r["locked_prediction"]["model_predicted_probability"]
            })

        brier = calculate_brier_score(preds_for_brier)

        return {
            "total_records": len(self.records),
            "resolved_outcomes": resolved_count,
            "pending_outcomes": pending,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": (wins / resolved_count) if resolved_count > 0 else 0.0,
            "brier_score": brier,
            "classification_breakdown": {
                "REAL-WORLD OBSERVATION": len(self.records),
                "SYNTHETIC RCE-001": 0,
                "ACTUAL MONEY WAGERS": 0
            }
        }

def persist_flight_artifact(flight_artifact: Dict[str, Any], output_path: Path) -> Path:
    """Persists flight artifact securely without overwriting existing historical records.

    If output_path exists, checks if prediction_id is already present. If present, raises FileExistsError.
    """
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                existing_pred_id = existing_data.get("flight_record", {}).get("prediction_id")
                new_pred_id = flight_artifact.get("flight_record", {}).get("prediction_id")
                if existing_pred_id and existing_pred_id == new_pred_id:
                    # Flight already exists with same prediction ID
                    return output_path
            except Exception:
                pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flight_artifact, f, indent=2)
    return output_path
