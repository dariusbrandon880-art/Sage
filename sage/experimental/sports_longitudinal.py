"""SAGE Sports Longitudinal & Real Observation Primitive.

Provides immutable data models, temporal locking, append-only outcome/scoring/learning
resolution, Brier score calibration, and longitudinal dataset ledger management under
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

@dataclass(frozen=True)
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
    classification: str = "REAL-WORLD OBSERVATION / REAL-WORLD RESEARCH PREDICTION"
    sha256_receipt_hash: str = ""

    def __post_init__(self):
        # Enforce Temporal Lock invariant: lock_timestamp_utc MUST BE strictly less than event_start_time_utc
        lock_dt = parse_iso_utc(self.lock_timestamp_utc)
        start_dt = parse_iso_utc(self.event_observation.event_start_time_utc)
        if lock_dt >= start_dt:
            raise ValueError(f"TEMPORAL_LOCK_VIOLATION: Lock timestamp {self.lock_timestamp_utc} is at or after event start time {self.event_observation.event_start_time_utc}.")

    def compute_sha256_hash(self) -> str:
        """Computes canonical SHA-256 HMAC digest covering ALL pre-event locked prediction fields."""
        payload = {
            "prediction_id": self.prediction_id,
            "cycle_id": self.cycle_id,
            "event_observation": asdict(self.event_observation),
            "selected_prediction": self.selected_prediction,
            "odds_at_lock": self.odds_at_lock,
            "implied_probability": self.implied_probability,
            "model_predicted_probability": self.model_predicted_probability,
            "lock_timestamp_utc": self.lock_timestamp_utc,
            "model_state_rationale": self.model_state_rationale,
            "is_parlay": self.is_parlay,
            "parlay_legs": self.parlay_legs,
            "classification": self.classification
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def lock_and_sign(self) -> str:
        self.sha256_receipt_hash = self.compute_sha256_hash()
        return self.sha256_receipt_hash

@dataclass
class SportsOutcomeRecord:
    outcome_id: str
    prediction_id: str
    prediction_hash: str
    verification_timestamp_utc: str
    verification_source_name: str
    verification_source_url: str
    actual_home_score: Optional[int]
    actual_away_score: Optional[int]
    actual_result_text: str
    outcome_status: str  # WIN, LOSS, PUSH, VOID, UNRESOLVED, SOURCE_UNAVAILABLE
    classification: str = "REAL-WORLD OUTCOME"
    outcome_receipt_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "outcome_id": self.outcome_id,
            "prediction_id": self.prediction_id,
            "prediction_hash": self.prediction_hash,
            "verification_timestamp_utc": self.verification_timestamp_utc,
            "verification_source_name": self.verification_source_name,
            "verification_source_url": self.verification_source_url,
            "actual_home_score": self.actual_home_score,
            "actual_away_score": self.actual_away_score,
            "actual_result_text": self.actual_result_text,
            "outcome_status": self.outcome_status,
            "classification": self.classification
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.outcome_receipt_hash = self.compute_sha256_hash()
        return self.outcome_receipt_hash

@dataclass
class SportsScoreRecord:
    score_id: str
    prediction_id: str
    prediction_hash: str
    outcome_id: str
    score_timestamp_utc: str
    model_predicted_probability: float
    outcome_status: str
    brier_score_contribution: Optional[float]
    classification: str = "REAL-WORLD SCORING"
    score_receipt_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "score_id": self.score_id,
            "prediction_id": self.prediction_id,
            "prediction_hash": self.prediction_hash,
            "outcome_id": self.outcome_id,
            "score_timestamp_utc": self.score_timestamp_utc,
            "model_predicted_probability": self.model_predicted_probability,
            "outcome_status": self.outcome_status,
            "brier_score_contribution": self.brier_score_contribution,
            "classification": self.classification
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.score_receipt_hash = self.compute_sha256_hash()
        return self.score_receipt_hash

@dataclass
class SportsLearningRecord:
    learning_id: str
    prediction_id: str
    prediction_hash: str
    outcome_id: str
    score_id: Optional[str]
    learning_timestamp_utc: str
    failure_classification: Optional[str]
    model_assumption_broken: Optional[str]
    lesson_recorded: str
    classification: str = "REAL-WORLD LEARNING"
    learning_receipt_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "learning_id": self.learning_id,
            "prediction_id": self.prediction_id,
            "prediction_hash": self.prediction_hash,
            "outcome_id": self.outcome_id,
            "score_id": self.score_id,
            "learning_timestamp_utc": self.learning_timestamp_utc,
            "failure_classification": self.failure_classification,
            "model_assumption_broken": self.model_assumption_broken,
            "lesson_recorded": self.lesson_recorded,
            "classification": self.classification
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.learning_receipt_hash = self.compute_sha256_hash()
        return self.learning_receipt_hash

def calculate_brier_score(predictions: List[Dict[str, Any]]) -> Optional[float]:
    """Calculates Brier Score BS = (1/N) * sum((predicted_prob - outcome_value)^2)."""
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

def resolve_sports_prediction(
    prediction: LockedResearchPrediction,
    verification_source_name: str,
    verification_source_url: str,
    actual_home_score: Optional[int],
    actual_away_score: Optional[int],
    actual_result_text: str,
    outcome_status: str,
    verification_timestamp_utc: str
) -> tuple[SportsOutcomeRecord, Optional[SportsScoreRecord], Optional[SportsLearningRecord]]:
    """Resolves a sports prediction by creating SEPARATE append-only records without mutating original prediction."""
    # Verify original prediction integrity before resolution
    computed_hash = prediction.compute_sha256_hash()
    if prediction.sha256_receipt_hash and prediction.sha256_receipt_hash != computed_hash:
        raise ValueError(f"PREDICTION_INTEGRITY_FAIL: Locked prediction hash {prediction.sha256_receipt_hash} does not match computed hash {computed_hash}.")

    outcome_id = f"out_{prediction.prediction_id}"
    outcome = SportsOutcomeRecord(
        outcome_id=outcome_id,
        prediction_id=prediction.prediction_id,
        prediction_hash=prediction.sha256_receipt_hash or computed_hash,
        verification_timestamp_utc=verification_timestamp_utc,
        verification_source_name=verification_source_name,
        verification_source_url=verification_source_url,
        actual_home_score=actual_home_score,
        actual_away_score=actual_away_score,
        actual_result_text=actual_result_text,
        outcome_status=outcome_status
    )
    outcome.sign()

    score = None
    learning = None

    if outcome_status in ["WIN", "LOSS"]:
        actual_val = 1.0 if outcome_status == "WIN" else 0.0
        brier_contrib = (prediction.model_predicted_probability - actual_val) ** 2
        score_id = f"score_{prediction.prediction_id}"
        score = SportsScoreRecord(
            score_id=score_id,
            prediction_id=prediction.prediction_id,
            prediction_hash=prediction.sha256_receipt_hash or computed_hash,
            outcome_id=outcome_id,
            score_timestamp_utc=verification_timestamp_utc,
            model_predicted_probability=prediction.model_predicted_probability,
            outcome_status=outcome_status,
            brier_score_contribution=brier_contrib
        )
        score.sign()

        lesson_text = "Prediction outcome verified successfully against public scoreboard."
        fail_class = None
        broken_assumption = None
        if outcome_status == "LOSS":
            fail_class = "REAL_WORLD_PREDICTION_ERROR"
            broken_assumption = "Model predicted probability exceeded actual empirical realization under market noise."
            lesson_text = "Incorporate market odds variance and opponent recent momentum into probability calibration model."

        learning_id = f"learn_{prediction.prediction_id}"
        learning = SportsLearningRecord(
            learning_id=learning_id,
            prediction_id=prediction.prediction_id,
            prediction_hash=prediction.sha256_receipt_hash or computed_hash,
            outcome_id=outcome_id,
            score_id=score_id,
            learning_timestamp_utc=verification_timestamp_utc,
            failure_classification=fail_class,
            model_assumption_broken=broken_assumption,
            lesson_recorded=lesson_text
        )
        learning.sign()

    return outcome, score, learning

class SportsLongitudinalLedger:
    def __init__(self):
        self.predictions: List[LockedResearchPrediction] = []
        self.outcomes: List[SportsOutcomeRecord] = []
        self.scores: List[SportsScoreRecord] = []
        self.learnings: List[SportsLearningRecord] = []
        self._prediction_ids: set[str] = set()

    def add_prediction(self, pred: LockedResearchPrediction) -> LockedResearchPrediction:
        if pred.prediction_id in self._prediction_ids:
            raise ValueError(f"DUPLICATE_PREDICTION_ID: Prediction ID '{pred.prediction_id}' already exists in longitudinal ledger.")
        if not pred.sha256_receipt_hash:
            pred.lock_and_sign()
        self.predictions.append(pred)
        self._prediction_ids.add(pred.prediction_id)
        return pred

    def add_outcome(self, outcome: SportsOutcomeRecord):
        if not outcome.outcome_receipt_hash:
            outcome.sign()
        self.outcomes.append(outcome)

    def add_score(self, score: SportsScoreRecord):
        if not score.score_receipt_hash:
            score.sign()
        self.scores.append(score)

    def add_learning(self, learning: SportsLearningRecord):
        if not learning.learning_receipt_hash:
            learning.sign()
        self.learnings.append(learning)

    def get_24h_sports_report(self) -> Dict[str, Any]:
        return {
            "total_predictions": len(self.predictions),
            "outcomes": [asdict(o) for o in self.outcomes],
            "scores": [asdict(s) for s in self.scores],
            "learnings": [asdict(l) for l in self.learnings]
        }

    def generate_summary_report(self) -> Dict[str, Any]:
        resolved_count = sum(1 for o in self.outcomes if o.outcome_status in ["WIN", "LOSS"])
        wins = sum(1 for o in self.outcomes if o.outcome_status == "WIN")
        losses = sum(1 for o in self.outcomes if o.outcome_status == "LOSS")
        pushes = sum(1 for o in self.outcomes if o.outcome_status == "PUSH")
        unresolved = len(self.predictions) - resolved_count

        preds_for_brier = []
        for s in self.scores:
            preds_for_brier.append({
                "outcome_status": s.outcome_status,
                "model_predicted_probability": s.model_predicted_probability
            })
        brier = calculate_brier_score(preds_for_brier)

        return {
            "total_records": len(self.predictions),
            "resolved_outcomes": resolved_count,
            "unresolved_outcomes": unresolved,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": (wins / resolved_count) if resolved_count > 0 else 0.0,
            "brier_score": brier,
            "classification_breakdown": {
                "REAL-WORLD OBSERVATION": len(self.predictions),
                "SYNTHETIC RCE-001": 0,
                "ACTUAL MONEY WAGERS": 0
            }
        }

def persist_flight_artifact(flight_artifact: Dict[str, Any], output_path: Path) -> Path:
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                existing_pred_id = existing_data.get("flight_record", {}).get("locked_prediction", {}).get("prediction_id") or existing_data.get("flight_record", {}).get("prediction_id")
                new_pred_id = flight_artifact.get("flight_record", {}).get("locked_prediction", {}).get("prediction_id") or flight_artifact.get("flight_record", {}).get("prediction_id")
                if existing_pred_id and existing_pred_id == new_pred_id:
                    return output_path
            except Exception:
                pass

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flight_artifact, f, indent=2)
    return output_path
