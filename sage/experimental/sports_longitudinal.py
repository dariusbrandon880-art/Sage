"""SAGE Sports Longitudinal & Real Observation Primitive.

Provides immutable data models, temporal locking, outcome resolution,
Brier score calibration, and longitudinal dataset ledger management under
Protected Sports/RCE Research Lane Governance.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import hashlib

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

    def add_entry(self, locked_pred: LockedResearchPrediction, outcome: RealOutcomeVerification) -> Dict[str, Any]:
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
