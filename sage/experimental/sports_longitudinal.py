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
    def __init__(self, storage_path: Optional[str | Path] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.predictions: List[LockedResearchPrediction] = []
        self.outcomes: List[SportsOutcomeRecord] = []
        self.scores: List[SportsScoreRecord] = []
        self.learnings: List[SportsLearningRecord] = []
        self._prediction_ids: set[str] = set()

        if self.storage_path and self.storage_path.exists():
            self.load(self.storage_path)

    def save(self, path: Optional[str | Path] = None) -> Path:
        target_path = Path(path) if path else self.storage_path
        if not target_path:
            raise ValueError("No storage path configured for ledger persistence.")

        data = {
            "predictions": [asdict(p) for p in self.predictions],
            "outcomes": [asdict(o) for o in self.outcomes],
            "scores": [asdict(s) for s in self.scores],
            "learnings": [asdict(l) for l in self.learnings]
        }
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return target_path

    def load(self, path: Optional[str | Path] = None) -> None:
        target_path = Path(path) if path else self.storage_path
        if not target_path or not target_path.exists():
            return

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.predictions.clear()
        self.outcomes.clear()
        self.scores.clear()
        self.learnings.clear()
        self._prediction_ids.clear()

        for raw_p in data.get("predictions", []):
            obs_data = raw_p.pop("event_observation")
            obs = RealSportsEventObservation(**obs_data)
            pred = LockedResearchPrediction(event_observation=obs, **raw_p)
            self.predictions.append(pred)
            self._prediction_ids.add(pred.prediction_id)

        for raw_o in data.get("outcomes", []):
            outcome = SportsOutcomeRecord(**raw_o)
            self.outcomes.append(outcome)

        for raw_s in data.get("scores", []):
            score = SportsScoreRecord(**raw_s)
            self.scores.append(score)

        for raw_l in data.get("learnings", []):
            learning = SportsLearningRecord(**raw_l)
            self.learnings.append(learning)

    def add_prediction(self, pred: LockedResearchPrediction) -> LockedResearchPrediction:
        if pred.prediction_id in self._prediction_ids:
            raise ValueError(f"DUPLICATE_PREDICTION_ID: Prediction ID '{pred.prediction_id}' already exists in longitudinal ledger.")
        if not pred.sha256_receipt_hash:
            pred.lock_and_sign()
        self.predictions.append(pred)
        self._prediction_ids.add(pred.prediction_id)
        if self.storage_path:
            self.save()
        return pred

    def add_outcome(self, outcome: SportsOutcomeRecord):
        existing_outcome = next((o for o in self.outcomes if o.prediction_id == outcome.prediction_id), None)
        if existing_outcome:
            raise ValueError(f"DUPLICATE_RESOLUTION_ATTEMPT: Prediction ID '{outcome.prediction_id}' already has a resolved outcome in ledger.")

        if not outcome.outcome_receipt_hash:
            outcome.sign()
        self.outcomes.append(outcome)
        if self.storage_path:
            self.save()

    def add_score(self, score: SportsScoreRecord):
        outcome_exists = any(o.outcome_id == score.outcome_id and o.prediction_id == score.prediction_id for o in self.outcomes)
        if not outcome_exists:
            raise ValueError(f"SCORE_WITHOUT_OUTCOME_FAIL: Cannot record score '{score.score_id}' without verified outcome.")

        if not score.score_receipt_hash:
            score.sign()
        self.scores.append(score)
        if self.storage_path:
            self.save()

    def add_learning(self, learning: SportsLearningRecord):
        score_exists = any(s.score_id == learning.score_id and s.prediction_id == learning.prediction_id for s in self.scores)
        if not score_exists:
            raise ValueError(f"LEARNING_WITHOUT_SCORE_FAIL: Cannot record learning '{learning.learning_id}' without valid score.")

        if not learning.learning_receipt_hash:
            learning.sign()
        self.learnings.append(learning)
        if self.storage_path:
            self.save()

    def get_pending_predictions(self) -> List[LockedResearchPrediction]:
        resolved_prediction_ids = {o.prediction_id for o in self.outcomes}
        return [p for p in self.predictions if p.prediction_id not in resolved_prediction_ids]

    def resolve_parlay_if_legs_complete(
        self,
        parlay_prediction_id: str,
        verification_source_name: str,
        verification_source_url: str,
        verification_timestamp_utc: str
    ) -> Optional[tuple[SportsOutcomeRecord, Optional[SportsScoreRecord], Optional[SportsLearningRecord]]]:
        parlay_pred = next((p for p in self.predictions if p.prediction_id == parlay_prediction_id), None)
        if not parlay_pred:
            raise KeyError(f"PARLAY_PREDICTION_NOT_FOUND: Parlay prediction '{parlay_prediction_id}' not found in ledger.")
        if not parlay_pred.is_parlay:
            raise ValueError(f"NOT_A_PARLAY: Prediction '{parlay_prediction_id}' is not marked as a parlay.")

        leg_ids = [leg.get("prediction_id") or leg.get("leg_id") for leg in parlay_pred.parlay_legs if leg.get("prediction_id") or leg.get("leg_id")]
        resolved_outcomes_by_id = {o.prediction_id: o for o in self.outcomes}

        # Check if all legs are resolved
        leg_outcomes = []
        for leg_id in leg_ids:
            if leg_id not in resolved_outcomes_by_id:
                # Parlay legs not yet complete
                return None
            leg_outcomes.append(resolved_outcomes_by_id[leg_id])

        # Evaluate parlay status
        if any(o.outcome_status == "LOSS" for o in leg_outcomes):
            parlay_status = "LOSS"
        elif all(o.outcome_status == "WIN" for o in leg_outcomes):
            parlay_status = "WIN"
        elif any(o.outcome_status == "PUSH" for o in leg_outcomes) and all(o.outcome_status in ["WIN", "PUSH"] for o in leg_outcomes):
            parlay_status = "PUSH"
        else:
            parlay_status = "UNRESOLVED"

        if parlay_status == "UNRESOLVED":
            return None

        result_summary = f"PARLAY_RESULT: {parlay_status} across {len(leg_ids)} legs."
        outcome, score, learning = resolve_sports_prediction(
            prediction=parlay_pred,
            verification_source_name=verification_source_name,
            verification_source_url=verification_source_url,
            actual_home_score=None,
            actual_away_score=None,
            actual_result_text=result_summary,
            outcome_status=parlay_status,
            verification_timestamp_utc=verification_timestamp_utc
        )
        self.add_outcome(outcome)
        if score:
            self.add_score(score)
        if learning:
            self.add_learning(learning)

        return outcome, score, learning

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


# =====================================================================
# RCE-002.4: OBSERVATION PROVENANCE, TEMPORAL CONSISTENCY & STREAM REPLAY
# =====================================================================

@dataclass
class ObservationProvenance:
    source_id: str
    source_name: str
    source_url: str
    source_timestamp_utc: str
    raw_payload_hash: str
    ingest_timestamp_utc: str
    provenance_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_timestamp_utc": self.source_timestamp_utc,
            "raw_payload_hash": self.raw_payload_hash,
            "ingest_timestamp_utc": self.ingest_timestamp_utc,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.provenance_hash = self.compute_sha256_hash()
        return self.provenance_hash


class TemporalConsistencyValidator:
    """Validates temporal monotonicity, lock boundary compliance, and prevents backdated/post-event leakage."""

    @staticmethod
    def validate_pre_game_observation(observation_timestamp_utc: str, event_start_time_utc: str) -> bool:
        obs_dt = parse_iso_utc(observation_timestamp_utc)
        start_dt = parse_iso_utc(event_start_time_utc)
        if obs_dt >= start_dt:
            raise ValueError(
                f"TEMPORAL_CONSISTENCY_VIOLATION: Observation time {observation_timestamp_utc} "
                f"is at or after event start time {event_start_time_utc}."
            )
        return True

    @staticmethod
    def validate_monotonic_sequence(timestamps_utc: List[str]) -> bool:
        if len(timestamps_utc) <= 1:
            return True
        for i in range(1, len(timestamps_utc)):
            prev_dt = parse_iso_utc(timestamps_utc[i - 1])
            curr_dt = parse_iso_utc(timestamps_utc[i])
            if curr_dt < prev_dt:
                raise ValueError(
                    f"TEMPORAL_MONOTONICITY_VIOLATION: Timestamp at index {i} ({timestamps_utc[i]}) "
                    f"is earlier than previous timestamp ({timestamps_utc[i - 1]})."
                )
        return True


@dataclass
class ObservationEvent:
    event_id: str
    observation_id: str
    observation_timestamp_utc: str
    event_start_time_utc: str
    provenance: ObservationProvenance
    payload: Dict[str, Any]
    previous_event_hash: str = ""
    event_hash: str = ""

    def compute_sha256_hash(self) -> str:
        prov_dict = asdict(self.provenance)
        payload_data = {
            "event_id": self.event_id,
            "observation_id": self.observation_id,
            "observation_timestamp_utc": self.observation_timestamp_utc,
            "event_start_time_utc": self.event_start_time_utc,
            "provenance": prov_dict,
            "payload": self.payload,
            "previous_event_hash": self.previous_event_hash,
        }
        serialized = json.dumps(payload_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.event_hash = self.compute_sha256_hash()
        return self.event_hash


class ReplayableObservationStream:
    """Provides append-only, temporally validated observation stream with hash-chained replay ability."""

    def __init__(self):
        self.stream: List[ObservationEvent] = []

    def append_event(
        self,
        event_id: str,
        observation_id: str,
        observation_timestamp_utc: str,
        event_start_time_utc: str,
        provenance: ObservationProvenance,
        payload: Dict[str, Any],
    ) -> ObservationEvent:
        # Validate temporal pre-game lock
        TemporalConsistencyValidator.validate_pre_game_observation(
            observation_timestamp_utc, event_start_time_utc
        )

        # Validate temporal monotonicity with existing stream
        if self.stream:
            last_ts = self.stream[-1].observation_timestamp_utc
            TemporalConsistencyValidator.validate_monotonic_sequence([last_ts, observation_timestamp_utc])
            prev_hash = self.stream[-1].event_hash
        else:
            prev_hash = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"

        if not provenance.provenance_hash:
            provenance.sign()

        obs_event = ObservationEvent(
            event_id=event_id,
            observation_id=observation_id,
            observation_timestamp_utc=observation_timestamp_utc,
            event_start_time_utc=event_start_time_utc,
            provenance=provenance,
            payload=payload,
            previous_event_hash=prev_hash,
        )
        obs_event.sign()
        self.stream.append(obs_event)
        return obs_event

    def verify_integrity(self) -> bool:
        if not self.stream:
            return True

        timestamps = [e.observation_timestamp_utc for e in self.stream]
        TemporalConsistencyValidator.validate_monotonic_sequence(timestamps)

        expected_prev = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"
        for idx, event in enumerate(self.stream):
            if event.previous_event_hash != expected_prev:
                raise ValueError(
                    f"STREAM_HASH_CHAIN_FAIL at index {idx}: Previous hash '{event.previous_event_hash}' "
                    f"does not match expected '{expected_prev}'."
                )
            computed_hash = event.compute_sha256_hash()
            if event.event_hash != computed_hash:
                raise ValueError(
                    f"STREAM_EVENT_HASH_TAMPERED at index {idx}: Stored '{event.event_hash}' "
                    f"differs from computed '{computed_hash}'."
                )
            expected_prev = event.event_hash

        return True

    def replay(self) -> List[Dict[str, Any]]:
        self.verify_integrity()
        replayed_state = []
        for idx, event in enumerate(self.stream):
            replayed_state.append({
                "replay_sequence": idx,
                "observation_id": event.observation_id,
                "event_id": event.event_id,
                "observation_timestamp_utc": event.observation_timestamp_utc,
                "provenance_source": event.provenance.source_name,
                "payload": event.payload,
                "verified_hash": event.event_hash,
            })
        return replayed_state
