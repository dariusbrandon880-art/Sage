"""SAGE Sports Longitudinal & Real Observation Primitive.

Provides immutable data models, temporal locking, append-only outcome/scoring/learning
resolution, Brier score calibration, and longitudinal dataset ledger management under
Protected Sports/RCE Research Lane Governance.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import hashlib
import time

class ObservationConfidenceLevel(str, Enum):
    OBS_0_UNKNOWN = "OBS-0 UNKNOWN"
    OBS_1_RECEIVED = "OBS-1 RECEIVED"
    OBS_2_IDENTIFIED = "OBS-2 IDENTIFIED"
    OBS_3_STATUS_VERIFIED = "OBS-3 STATUS VERIFIED"
    OBS_4_FINALITY_VERIFIED = "OBS-4 FINALITY VERIFIED"
    OBS_5_RESOLUTION_VERIFIED = "OBS-5 RESOLUTION VERIFIED"

class ObservationAgreementState(str, Enum):
    OBS_MATCHED = "OBS_MATCHED"
    OBS_MINOR_VARIANCE = "OBS_MINOR_VARIANCE"
    OBS_CONFLICT = "OBS_CONFLICT"
    OBS_UNAVAILABLE = "OBS_UNAVAILABLE"
    OBS_PENDING = "OBS_PENDING"

class ObservationReliabilityGrade(str, Enum):
    RELIABILITY_UNKNOWN = "RELIABILITY_UNKNOWN"
    RELIABILITY_LOW = "RELIABILITY_LOW"
    RELIABILITY_MODERATE = "RELIABILITY_MODERATE"
    RELIABILITY_HIGH = "RELIABILITY_HIGH"
    RELIABILITY_VERIFIED = "RELIABILITY_VERIFIED"

class ObservationTemporalClassification(str, Enum):
    TEMPORAL_UNKNOWN = "TEMPORAL_UNKNOWN"
    TEMPORAL_CURRENT = "TEMPORAL_CURRENT"
    TEMPORAL_LATE = "TEMPORAL_LATE"
    TEMPORAL_DUPLICATE = "TEMPORAL_DUPLICATE"
    TEMPORAL_CORRECTED = "TEMPORAL_CORRECTED"
    TEMPORAL_CONFLICTED = "TEMPORAL_CONFLICTED"
    TEMPORAL_FINAL = "TEMPORAL_FINAL"

class SportsObservationEventType(str, Enum):
    OBS_RECEIVED = "OBS_RECEIVED"
    OBS_STATUS_CHANGED = "OBS_STATUS_CHANGED"
    OBS_CONFLICT_DETECTED = "OBS_CONFLICT_DETECTED"
    OBS_ARBITRATED = "OBS_ARBITRATED"
    OBS_FINALIZED = "OBS_FINALIZED"
    OBS_CORRECTED = "OBS_CORRECTED"
    OBS_RECONCILED = "OBS_RECONCILED"

class ObservationAvailabilityClassification(str, Enum):
    AVAILABLE = "AVAILABLE"
    AVAILABLE_AFTER_RESEARCH_TIME = "AVAILABLE_AFTER_RESEARCH_TIME"
    LATE_OBSERVATION = "LATE_OBSERVATION"
    CORRECTION_NOT_AVAILABLE_AT_T = "CORRECTION_NOT_AVAILABLE_AT_T"
    POST_TIMESTAMP_LEAKAGE = "POST_TIMESTAMP_LEAKAGE"
    FAIL_CLOSED_AMBIGUOUS_TIMING = "FAIL_CLOSED_AMBIGUOUS_TIMING"

@dataclass
class ObservationAvailabilitySnapshot:
    snapshot_id: str
    research_timestamp_utc: str
    total_observations_analyzed: int
    available_observations: List[Dict[str, Any]]
    excluded_observations: List[Dict[str, Any]]
    leakage_detected: bool
    classification_breakdown: Dict[str, int]
    sha256_hash: str = ""

    def __post_init__(self):
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "research_timestamp_utc": self.research_timestamp_utc,
            "total_observations_analyzed": self.total_observations_analyzed,
            "available_observations": self.available_observations,
            "excluded_observations": self.excluded_observations,
            "leakage_detected": self.leakage_detected,
            "classification_breakdown": self.classification_breakdown
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class HistoricalResearchSnapshot:
    snapshot_id: str
    research_timestamp_utc: str
    event_identities: List[str]
    included_observation_references: List[str]
    excluded_post_timestamp_references: List[str]
    effective_observation_state: Dict[str, Any]
    source_conflict_references: List[str]
    snapshot_hash: str = ""
    creation_reference: str = ""
    integrity_hash: str = ""

    def __post_init__(self):
        if not self.snapshot_hash:
            self.snapshot_hash = self.compute_snapshot_hash()
        if not self.creation_reference:
            self.creation_reference = f"created_at_{self.research_timestamp_utc}"
        if not self.integrity_hash:
            self.integrity_hash = self.compute_integrity_hash()

    def compute_snapshot_hash(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "research_timestamp_utc": self.research_timestamp_utc,
            "event_identities": sorted(self.event_identities),
            "included_observation_references": sorted(self.included_observation_references),
            "excluded_post_timestamp_references": sorted(self.excluded_post_timestamp_references),
            "effective_observation_state": self.effective_observation_state,
            "source_conflict_references": sorted(self.source_conflict_references)
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def compute_integrity_hash(self) -> str:
        payload = {
            "snapshot_hash": self.snapshot_hash,
            "creation_reference": self.creation_reference,
            "research_timestamp_utc": self.research_timestamp_utc
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class ResearchIntegrityReceipt:
    receipt_id: str
    snapshot_id: str
    research_timestamp_utc: str
    observed_reference_set: List[str]
    post_timestamp_reference_set: List[str]
    excluded_count: int
    integrity_status: str  # RESEARCH_TIME_CLEAN, POST_TIMESTAMP_INFORMATION_DETECTED, AMBIGUOUS_AVAILABILITY, INTEGRITY_FAILURE
    reason: str
    snapshot_hash: str
    integrity_hash: str = ""

    def __post_init__(self):
        if not self.integrity_hash:
            self.integrity_hash = self.compute_integrity_hash()

    def compute_integrity_hash(self) -> str:
        payload = {
            "receipt_id": self.receipt_id,
            "snapshot_id": self.snapshot_id,
            "research_timestamp_utc": self.research_timestamp_utc,
            "observed_reference_set": sorted(self.observed_reference_set),
            "post_timestamp_reference_set": sorted(self.post_timestamp_reference_set),
            "excluded_count": self.excluded_count,
            "integrity_status": self.integrity_status,
            "reason": self.reason,
            "snapshot_hash": self.snapshot_hash
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class SportsObservationEvent:
    event_stream_id: str
    sequence_number: int
    event_type: str
    provider: str
    external_event_id: str
    timestamp_utc: str
    payload_hash: str
    details: Dict[str, Any] = field(default_factory=dict)
    sha256_hash: str = ""

    def __post_init__(self):
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "event_stream_id": self.event_stream_id,
            "sequence_number": self.sequence_number,
            "event_type": self.event_type,
            "provider": self.provider,
            "external_event_id": self.external_event_id,
            "timestamp_utc": self.timestamp_utc,
            "payload_hash": self.payload_hash,
            "details": self.details
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class ObservationTemporalRecord:
    temporal_id: str
    provider: str
    external_event_id: str
    observation_timestamp_utc: str
    retrieval_timestamp_utc: str
    provider_status: str
    observation_confidence: str
    source_payload_hash: str
    prior_observation_reference: Optional[str] = None
    transition_detected: bool = False
    correction_detected: bool = False
    finality_state: bool = False
    temporal_classification: str = ObservationTemporalClassification.TEMPORAL_UNKNOWN.value
    observation_delay_seconds: float = 0.0
    sha256_hash: str = ""

    def __post_init__(self):
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "temporal_id": self.temporal_id,
            "provider": self.provider,
            "external_event_id": self.external_event_id,
            "observation_timestamp_utc": self.observation_timestamp_utc,
            "retrieval_timestamp_utc": self.retrieval_timestamp_utc,
            "provider_status": self.provider_status,
            "observation_confidence": self.observation_confidence,
            "source_payload_hash": self.source_payload_hash,
            "prior_observation_reference": self.prior_observation_reference or "",
            "transition_detected": self.transition_detected,
            "correction_detected": self.correction_detected,
            "finality_state": self.finality_state,
            "temporal_classification": self.temporal_classification,
            "observation_delay_seconds": self.observation_delay_seconds
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class ProviderReliabilityRecord:
    provider: str
    event_observations_attempted: int = 0
    successful_observations: int = 0
    failed_observations: int = 0
    conflicts_generated: int = 0
    finality_accuracy: float = 1.0
    average_resolution_delay_seconds: float = 0.0
    duplicate_rate: float = 0.0
    stale_observation_rate: float = 0.0
    availability_rate: float = 1.0
    last_observed_timestamp_utc: str = ""
    reliability_grade: str = ObservationReliabilityGrade.RELIABILITY_UNKNOWN.value
    sha256_hash: str = ""

    def __post_init__(self):
        self.update_grade()
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def update_grade(self) -> str:
        if self.event_observations_attempted == 0:
            self.reliability_grade = ObservationReliabilityGrade.RELIABILITY_UNKNOWN.value
        elif self.availability_rate < 0.80 or self.finality_accuracy < 0.80 or self.conflicts_generated >= 5:
            self.reliability_grade = ObservationReliabilityGrade.RELIABILITY_LOW.value
        elif self.availability_rate < 0.92 or self.finality_accuracy < 0.92:
            self.reliability_grade = ObservationReliabilityGrade.RELIABILITY_MODERATE.value
        elif self.availability_rate >= 0.98 and self.finality_accuracy >= 0.98 and self.conflicts_generated == 0 and self.event_observations_attempted >= 3:
            self.reliability_grade = ObservationReliabilityGrade.RELIABILITY_VERIFIED.value
        else:
            self.reliability_grade = ObservationReliabilityGrade.RELIABILITY_HIGH.value
        return self.reliability_grade

    def compute_sha256(self) -> str:
        payload = {
            "provider": self.provider,
            "event_observations_attempted": self.event_observations_attempted,
            "successful_observations": self.successful_observations,
            "failed_observations": self.failed_observations,
            "conflicts_generated": self.conflicts_generated,
            "finality_accuracy": self.finality_accuracy,
            "average_resolution_delay_seconds": self.average_resolution_delay_seconds,
            "duplicate_rate": self.duplicate_rate,
            "stale_observation_rate": self.stale_observation_rate,
            "availability_rate": self.availability_rate,
            "last_observed_timestamp_utc": self.last_observed_timestamp_utc,
            "reliability_grade": self.reliability_grade
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class SourceObservation:
    provider: str
    event_id: str
    retrieval_timestamp_utc: str
    raw_payload_hash: str
    observed_status: str
    home_score: Optional[int]
    away_score: Optional[int]
    is_final: bool

@dataclass
class ObservationArbitrationReceipt:
    arbitration_id: str
    prediction_id: str
    external_event_id: str
    timestamp_utc: str
    agreement_state: str
    observations: List[Dict[str, Any]]
    resolution_allowed: bool
    rationale: str
    sha256_hash: str = ""

    def __post_init__(self):
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "arbitration_id": self.arbitration_id,
            "prediction_id": self.prediction_id,
            "external_event_id": self.external_event_id,
            "timestamp_utc": self.timestamp_utc,
            "agreement_state": self.agreement_state,
            "observations": self.observations,
            "resolution_allowed": self.resolution_allowed,
            "rationale": self.rationale
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

@dataclass
class ReconciliationQualityTelemetry:
    telemetry_id: str
    prediction_id: str
    provider_used: str
    query_timestamp_utc: str
    external_event_id: str
    response_latency_ms: float
    response_validity: bool
    observation_confidence: str
    finality_transition_observed: str
    resolution_delay_seconds: Optional[float]
    reconciliation_attempts: int
    failure_category: Optional[str] = None
    sha256_telemetry_hash: str = ""

    def __post_init__(self):
        if not self.sha256_telemetry_hash:
            self.sha256_telemetry_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "telemetry_id": self.telemetry_id,
            "prediction_id": self.prediction_id,
            "provider_used": self.provider_used,
            "query_timestamp_utc": self.query_timestamp_utc,
            "external_event_id": self.external_event_id,
            "response_latency_ms": self.response_latency_ms,
            "response_validity": self.response_validity,
            "observation_confidence": self.observation_confidence,
            "finality_transition_observed": self.finality_transition_observed,
            "resolution_delay_seconds": self.resolution_delay_seconds,
            "reconciliation_attempts": self.reconciliation_attempts,
            "failure_category": self.failure_category or ""
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

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
        self.quality_telemetry: List[ReconciliationQualityTelemetry] = []
        self.arbitration_history: List[ObservationArbitrationReceipt] = []
        self.provider_reliability: Dict[str, ProviderReliabilityRecord] = {}
        self.temporal_observations: List[ObservationTemporalRecord] = []
        self.observation_event_stream: List[SportsObservationEvent] = []
        self.processed_receipt_ids: set[str] = set()
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
            "learnings": [asdict(l) for l in self.learnings],
            "quality_telemetry": [asdict(q) for q in self.quality_telemetry],
            "arbitration_history": [asdict(a) for a in self.arbitration_history],
            "provider_reliability": {k: asdict(v) for k, v in self.provider_reliability.items()},
            "temporal_observations": [asdict(t) for t in self.temporal_observations],
            "observation_event_stream": [asdict(e) for e in self.observation_event_stream],
            "processed_receipt_ids": list(self.processed_receipt_ids)
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
        self.quality_telemetry.clear()
        self.arbitration_history.clear()
        self.provider_reliability.clear()
        self.temporal_observations.clear()
        self.observation_event_stream.clear()
        self.processed_receipt_ids.clear()
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

        for raw_q in data.get("quality_telemetry", []):
            telemetry = ReconciliationQualityTelemetry(**raw_q)
            self.quality_telemetry.append(telemetry)

        for raw_a in data.get("arbitration_history", []):
            receipt = ObservationArbitrationReceipt(**raw_a)
            self.arbitration_history.append(receipt)

        for p_name, raw_r in data.get("provider_reliability", {}).items():
            record = ProviderReliabilityRecord(**raw_r)
            self.provider_reliability[p_name] = record

        for raw_t in data.get("temporal_observations", []):
            temp_rec = ObservationTemporalRecord(**raw_t)
            self.temporal_observations.append(temp_rec)

        for raw_e in data.get("observation_event_stream", []):
            event_rec = SportsObservationEvent(**raw_e)
            self.observation_event_stream.append(event_rec)

        self.processed_receipt_ids = set(data.get("processed_receipt_ids", []))

    def add_arbitration_receipt(self, receipt: ObservationArbitrationReceipt):
        self.arbitration_history.append(receipt)
        if self.storage_path:
            self.save()

    def add_quality_telemetry(self, telemetry: ReconciliationQualityTelemetry):
        self.quality_telemetry.append(telemetry)
        if self.storage_path:
            self.save()

    def get_reconciliation_attempts_count(self, prediction_id: str) -> int:
        return sum(1 for q in self.quality_telemetry if q.prediction_id == prediction_id)

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


@dataclass
class ReconciliationRunReceipt:
    reconciliation_id: str
    timestamp_utc: str
    polled_count: int
    resolved_single_count: int
    resolved_parlay_count: int
    remaining_pending_count: int
    summary_report: Dict[str, Any]
    sha256_receipt_hash: str = ""

    def __post_init__(self):
        if not self.sha256_receipt_hash:
            self.sha256_receipt_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        payload = {
            "reconciliation_id": self.reconciliation_id,
            "timestamp_utc": self.timestamp_utc,
            "polled_count": self.polled_count,
            "resolved_single_count": self.resolved_single_count,
            "resolved_parlay_count": self.resolved_parlay_count,
            "remaining_pending_count": self.remaining_pending_count,
            "summary_report": self.summary_report
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SportsOutcomeReconciler:
    """Automated, idempotent outcome polling and reconciliation engine for SportsLongitudinalLedger."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def poll_and_reconcile(
        self,
        custom_fetcher: Optional[Any] = None,
        reference_time_utc: Optional[str] = None
    ) -> ReconciliationRunReceipt:
        now_ts = reference_time_utc or datetime.now(timezone.utc).isoformat()
        pending_preds = self.ledger.get_pending_predictions()
        polled_count = len(pending_preds)
        resolved_single = 0
        resolved_parlay = 0

        # 1. Process non-parlay pending predictions first
        for pred in pending_preds:
            if pred.is_parlay:
                continue

            event = pred.event_observation
            attempts = self.ledger.get_reconciliation_attempts_count(pred.prediction_id) + 1
            t_start = time.perf_counter()

            game_result = None
            response_validity = False
            failure_category = None
            confidence = ObservationConfidenceLevel.OBS_0_UNKNOWN.value
            finality_transition = "NONE"

            try:
                if custom_fetcher:
                    game_result = custom_fetcher(event)
                if game_result and isinstance(game_result, dict):
                    response_validity = True
                    confidence = ObservationConfidenceLevel.OBS_1_RECEIVED.value
                    if game_result.get("event_id") or event.event_id:
                        confidence = ObservationConfidenceLevel.OBS_2_IDENTIFIED.value
                    if "is_final" in game_result or "abstractGameState" in game_result:
                        confidence = ObservationConfidenceLevel.OBS_3_STATUS_VERIFIED.value
                else:
                    failure_category = "MALFORMED_RESPONSE"
            except Exception as e:
                response_validity = False
                failure_category = f"PROVIDER_ERROR_{e.__class__.__name__}"

            t_end = time.perf_counter()
            latency_ms = round((t_end - t_start) * 1000, 2)

            resolved_now = False
            res_delay_sec = None

            if response_validity and game_result and game_result.get("is_final"):
                confidence = ObservationConfidenceLevel.OBS_4_FINALITY_VERIFIED.value
                finality_transition = f"{event.event_status}->FINAL"

                home_score = game_result.get("home_score")
                away_score = game_result.get("away_score")
                result_text = game_result.get("result_text", "Game Completed")

                outcome_status = "UNRESOLVED"
                selection = pred.selected_prediction.lower()
                if "moneyline" in selection:
                    if event.home_team.lower() in selection:
                        if home_score is not None and away_score is not None:
                            outcome_status = "WIN" if home_score > away_score else ("LOSS" if away_score > home_score else "PUSH")
                    elif event.away_team.lower() in selection:
                        if home_score is not None and away_score is not None:
                            outcome_status = "WIN" if away_score > home_score else ("LOSS" if home_score > away_score else "PUSH")
                elif game_result.get("outcome_status"):
                    outcome_status = game_result.get("outcome_status")

                if outcome_status in ["WIN", "LOSS", "PUSH"]:
                    outcome, score, learning = resolve_sports_prediction(
                        prediction=pred,
                        verification_source_name=event.source_name,
                        verification_source_url=event.source_url,
                        actual_home_score=home_score,
                        actual_away_score=away_score,
                        actual_result_text=result_text,
                        outcome_status=outcome_status,
                        verification_timestamp_utc=now_ts
                    )
                    try:
                        self.ledger.add_outcome(outcome)
                        if score:
                            self.ledger.add_score(score)
                        if learning:
                            self.ledger.add_learning(learning)
                        resolved_single += 1
                        resolved_now = True
                        confidence = ObservationConfidenceLevel.OBS_5_RESOLUTION_VERIFIED.value

                        try:
                            start_dt = parse_iso_utc(event.event_start_time_utc)
                            verif_dt = parse_iso_utc(now_ts)
                            res_delay_sec = round((verif_dt - start_dt).total_seconds(), 2)
                        except Exception:
                            res_delay_sec = 0.0
                    except ValueError:
                        # Fail-closed / skip duplicate
                        pass

            # Create and append Quality Telemetry
            telemetry = ReconciliationQualityTelemetry(
                telemetry_id=f"qual_{pred.prediction_id}_{attempts}",
                prediction_id=pred.prediction_id,
                provider_used=event.source_name,
                query_timestamp_utc=now_ts,
                external_event_id=event.event_id,
                response_latency_ms=latency_ms,
                response_validity=response_validity,
                observation_confidence=confidence,
                finality_transition_observed=finality_transition,
                resolution_delay_seconds=res_delay_sec,
                reconciliation_attempts=attempts,
                failure_category=failure_category
            )
            self.ledger.add_quality_telemetry(telemetry)

        # 2. Process parlay pending predictions whose legs may now be resolved
        for pred in pending_preds:
            if not pred.is_parlay:
                continue

            try:
                parlay_res = self.ledger.resolve_parlay_if_legs_complete(
                    parlay_prediction_id=pred.prediction_id,
                    verification_source_name="SAGE Parlay Reconciler",
                    verification_source_url=pred.event_observation.source_url,
                    verification_timestamp_utc=now_ts
                )
                if parlay_res:
                    resolved_parlay += 1
            except (KeyError, ValueError):
                pass

        remaining_pending = len(self.ledger.get_pending_predictions())
        summary = self.ledger.generate_summary_report()

        receipt_id = f"recon_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        return ReconciliationRunReceipt(
            reconciliation_id=receipt_id,
            timestamp_utc=now_ts,
            polled_count=polled_count,
            resolved_single_count=resolved_single,
            resolved_parlay_count=resolved_parlay,
            remaining_pending_count=remaining_pending,
            summary_report=summary
        )


class SportsObservationArbitrator:
    """Multi-source observation arbitration layer enforcing consensus before outcome resolution."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def arbitrate_observations(
        self,
        prediction_id: str,
        observations: List[SourceObservation],
        reference_time_utc: Optional[str] = None
    ) -> ObservationArbitrationReceipt:
        now_ts = reference_time_utc or datetime.now(timezone.utc).isoformat()
        pred = next((p for p in self.ledger.predictions if p.prediction_id == prediction_id), None)
        if not pred:
            raise KeyError(f"PREDICTION_NOT_FOUND: Prediction ID '{prediction_id}' not found in ledger.")

        ext_event_id = pred.event_observation.event_id
        obs_dicts = [asdict(obs) for obs in observations]

        if not observations:
            receipt = ObservationArbitrationReceipt(
                arbitration_id=f"arb_{prediction_id}_{datetime.now(timezone.utc).strftime('%H%M%S')}",
                prediction_id=prediction_id,
                external_event_id=ext_event_id,
                timestamp_utc=now_ts,
                agreement_state=ObservationAgreementState.OBS_UNAVAILABLE.value,
                observations=[],
                resolution_allowed=False,
                rationale="Zero provider observations available."
            )
            self.ledger.add_arbitration_receipt(receipt)
            return receipt

        # Evaluate multi-source consensus
        finalities = {obs.is_final for obs in observations}
        home_scores = {obs.home_score for obs in observations if obs.home_score is not None}
        away_scores = {obs.away_score for obs in observations if obs.away_score is not None}

        if len(finalities) > 1 or len(home_scores) > 1 or len(away_scores) > 1:
            state = ObservationAgreementState.OBS_CONFLICT.value
            res_allowed = False
            rationale = "CONFLICT_DETECTED: Disagreement observed across provider status or score payloads. Resolution blocked."
        elif True in finalities and len(home_scores) == 1 and len(away_scores) == 1:
            state = ObservationAgreementState.OBS_MATCHED.value
            res_allowed = True
            rationale = "CONSENSUS_MATCHED: Multi-source agreement verified for game finality and score."
        else:
            state = ObservationAgreementState.OBS_PENDING.value
            res_allowed = False
            rationale = "GAME_IN_PROGRESS_OR_PREVIEW: All providers observe game as non-final."

        receipt = ObservationArbitrationReceipt(
            arbitration_id=f"arb_{prediction_id}_{datetime.now(timezone.utc).strftime('%H%M%S')}",
            prediction_id=prediction_id,
            external_event_id=ext_event_id,
            timestamp_utc=now_ts,
            agreement_state=state,
            observations=obs_dicts,
            resolution_allowed=res_allowed,
            rationale=rationale
        )
        self.ledger.add_arbitration_receipt(receipt)

        # Execute resolution if allowed and matched
        if res_allowed and state == ObservationAgreementState.OBS_MATCHED:
            h_score = list(home_scores)[0]
            a_score = list(away_scores)[0]
            event = pred.event_observation

            selection = pred.selected_prediction.lower()
            outcome_status = "UNRESOLVED"
            if "moneyline" in selection:
                if event.home_team.lower() in selection:
                    outcome_status = "WIN" if h_score > a_score else ("LOSS" if a_score > h_score else "PUSH")
                elif event.away_team.lower() in selection:
                    outcome_status = "WIN" if a_score > h_score else ("LOSS" if h_score > a_score else "PUSH")

            if outcome_status in ["WIN", "LOSS", "PUSH"]:
                outcome, score, learning = resolve_sports_prediction(
                    prediction=pred,
                    verification_source_name=f"Arbitrated ({len(observations)} sources)",
                    verification_source_url=event.source_url,
                    actual_home_score=h_score,
                    actual_away_score=a_score,
                    actual_result_text=f"Arbitrated Result: {event.home_team} {h_score}, {event.away_team} {a_score}",
                    outcome_status=outcome_status,
                    verification_timestamp_utc=now_ts
                )
                try:
                    self.ledger.add_outcome(outcome)
                    if score:
                        self.ledger.add_score(score)
                    if learning:
                        self.ledger.add_learning(learning)
                except ValueError:
                    pass

        return receipt


class ObservationReliabilityLedger:
    """Measurement layer tracking historical reliability, conflict rate, and availability per sports observation provider."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def ingest_arbitration_receipt(self, receipt: ObservationArbitrationReceipt) -> Dict[str, ProviderReliabilityRecord]:
        if not receipt or not receipt.arbitration_id:
            raise ValueError("RECEIPT_REQUIRED_FOR_RELIABILITY_UPDATE: Cannot update provider reliability without a valid arbitration receipt.")

        if receipt.arbitration_id in self.ledger.processed_receipt_ids:
            # Idempotent skip: receipt already processed
            return self.ledger.provider_reliability

        for obs in receipt.observations:
            provider_name = obs.get("provider", "UNKNOWN_PROVIDER")
            rec = self.ledger.provider_reliability.get(provider_name)
            if not rec:
                rec = ProviderReliabilityRecord(provider=provider_name)
                self.ledger.provider_reliability[provider_name] = rec

            rec.event_observations_attempted += 1
            rec.successful_observations += 1
            if receipt.agreement_state == ObservationAgreementState.OBS_CONFLICT.value:
                rec.conflicts_generated += 1

            rec.last_observed_timestamp_utc = receipt.timestamp_utc
            rec.availability_rate = round(rec.successful_observations / rec.event_observations_attempted, 4)
            if rec.event_observations_attempted > 0:
                rec.finality_accuracy = round((rec.event_observations_attempted - rec.conflicts_generated) / rec.event_observations_attempted, 4)
            rec.update_grade()
            rec.sha256_hash = rec.compute_sha256()

        self.ledger.processed_receipt_ids.add(receipt.arbitration_id)
        if self.ledger.storage_path:
            self.ledger.save()

        return self.ledger.provider_reliability

    def ingest_quality_telemetry(self, telemetry: ReconciliationQualityTelemetry, receipt_id: str) -> ProviderReliabilityRecord:
        if not receipt_id:
            raise ValueError("RECEIPT_REQUIRED_FOR_RELIABILITY_UPDATE: Telemetry update requires a valid reconciliation receipt ID.")

        unique_key = f"{receipt_id}_{telemetry.telemetry_id}"
        if unique_key in self.ledger.processed_receipt_ids:
            return self.ledger.provider_reliability.get(telemetry.provider_used, ProviderReliabilityRecord(provider=telemetry.provider_used))

        provider_name = telemetry.provider_used
        rec = self.ledger.provider_reliability.get(provider_name)
        if not rec:
            rec = ProviderReliabilityRecord(provider=provider_name)
            self.ledger.provider_reliability[provider_name] = rec

        rec.event_observations_attempted += 1
        if telemetry.response_validity:
            rec.successful_observations += 1
        else:
            rec.failed_observations += 1

        rec.last_observed_timestamp_utc = telemetry.query_timestamp_utc
        rec.availability_rate = round(rec.successful_observations / rec.event_observations_attempted, 4)
        rec.update_grade()
        rec.sha256_hash = rec.compute_sha256()

        self.ledger.processed_receipt_ids.add(unique_key)
        if self.ledger.storage_path:
            self.ledger.save()

        return rec

    def get_provider_grade(self, provider_name: str) -> str:
        rec = self.ledger.provider_reliability.get(provider_name)
        if not rec:
            return ObservationReliabilityGrade.RELIABILITY_UNKNOWN.value
        return rec.reliability_grade


class ObservationTemporalLedger:
    """Event-level and temporal observation integrity ledger tracking source chronology, transitions, and corrections."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def record_temporal_observation(
        self,
        obs: SourceObservation,
        observation_confidence: str = ObservationConfidenceLevel.OBS_3_STATUS_VERIFIED.value
    ) -> ObservationTemporalRecord:
        if not obs.provider or not obs.event_id:
            raise ValueError("UNKNOWN_EVENT_IDENTITY: Provider and external event ID are required for temporal observation recording.")

        # Query existing temporal observation chronology for this provider + external event
        prior_records = [
            t for t in self.ledger.temporal_observations
            if t.provider == obs.provider and t.external_event_id == obs.event_id
        ]
        prior_ref = prior_records[-1].temporal_id if prior_records else None

        transition_detected = False
        correction_detected = False
        finality_state = obs.is_final
        classification = ObservationTemporalClassification.TEMPORAL_CURRENT.value

        # Calculate observation delay
        delay_sec = 0.0
        try:
            obs_dt = parse_iso_utc(obs.retrieval_timestamp_utc)
            ret_dt = parse_iso_utc(obs.retrieval_timestamp_utc)
            delay_sec = max(0.0, (ret_dt - obs_dt).total_seconds())
        except Exception:
            pass

        if prior_records:
            latest_prior = prior_records[-1]

            if latest_prior.source_payload_hash == obs.raw_payload_hash:
                classification = ObservationTemporalClassification.TEMPORAL_DUPLICATE.value
            elif latest_prior.finality_state and not obs.is_final:
                classification = ObservationTemporalClassification.TEMPORAL_CONFLICTED.value
            elif latest_prior.finality_state and obs.is_final and latest_prior.source_payload_hash != obs.raw_payload_hash:
                classification = ObservationTemporalClassification.TEMPORAL_CORRECTED.value
                correction_detected = True
            elif latest_prior.provider_status != obs.observed_status or latest_prior.finality_state != obs.is_final:
                transition_detected = True
                classification = ObservationTemporalClassification.TEMPORAL_FINAL.value if obs.is_final else ObservationTemporalClassification.TEMPORAL_CURRENT.value
            elif obs.is_final:
                classification = ObservationTemporalClassification.TEMPORAL_FINAL.value
        elif obs.is_final:
            classification = ObservationTemporalClassification.TEMPORAL_FINAL.value

        record = ObservationTemporalRecord(
            temporal_id=f"temp_{obs.provider}_{obs.event_id}_{len(prior_records) + 1}",
            provider=obs.provider,
            external_event_id=obs.event_id,
            observation_timestamp_utc=obs.retrieval_timestamp_utc,
            retrieval_timestamp_utc=obs.retrieval_timestamp_utc,
            provider_status=obs.observed_status,
            observation_confidence=observation_confidence,
            source_payload_hash=obs.raw_payload_hash,
            prior_observation_reference=prior_ref,
            transition_detected=transition_detected,
            correction_detected=correction_detected,
            finality_state=finality_state,
            temporal_classification=classification,
            observation_delay_seconds=delay_sec
        )

        self.ledger.temporal_observations.append(record)
        if self.ledger.storage_path:
            self.ledger.save()

        return record


class SportsObservationEventStream:
    """Append-only, deterministic observation event stream and projection replay engine."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def append_event(
        self,
        event_type: str,
        provider: str,
        external_event_id: str,
        payload_hash: str,
        details: Dict[str, Any],
        timestamp_utc: Optional[str] = None
    ) -> SportsObservationEvent:
        if not provider or not external_event_id:
            raise ValueError("EVENT_STREAM_IDENTITY_FAIL: Provider and external event ID are required for event stream append.")

        now_ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
        prior_events = [
            e for e in self.ledger.observation_event_stream
            if e.provider == provider and e.external_event_id == external_event_id
        ]
        seq_num = len(prior_events) + 1
        stream_id = f"stream_{provider}_{external_event_id}_{seq_num}"

        event = SportsObservationEvent(
            event_stream_id=stream_id,
            sequence_number=seq_num,
            event_type=event_type,
            provider=provider,
            external_event_id=external_event_id,
            timestamp_utc=now_ts,
            payload_hash=payload_hash,
            details=details
        )

        self.ledger.observation_event_stream.append(event)
        if self.ledger.storage_path:
            self.ledger.save()

        return event

    def reconstruct_event_state(self, external_event_id: str) -> Dict[str, Any]:
        """Deterministically replays all stream events for an external_event_id to project current state."""
        events = [
            e for e in self.ledger.observation_event_stream
            if e.external_event_id == external_event_id
        ]
        events_sorted = sorted(events, key=lambda x: (x.sequence_number, x.timestamp_utc))

        providers_observed = set()
        latest_status_by_provider: Dict[str, str] = {}
        latest_scores_by_provider: Dict[str, Dict[str, Any]] = {}
        is_finalized = False
        conflicts_detected = 0
        corrections_count = 0
        chronology = []

        for e in events_sorted:
            providers_observed.add(e.provider)
            latest_status_by_provider[e.provider] = e.details.get("status", "UNKNOWN")

            if "home_score" in e.details or "away_score" in e.details:
                latest_scores_by_provider[e.provider] = {
                    "home_score": e.details.get("home_score"),
                    "away_score": e.details.get("away_score")
                }

            if e.event_type == SportsObservationEventType.OBS_FINALIZED.value or e.details.get("is_final") is True:
                is_finalized = True

            if e.event_type == SportsObservationEventType.OBS_CONFLICT_DETECTED.value:
                conflicts_detected += 1

            if e.event_type == SportsObservationEventType.OBS_CORRECTED.value:
                corrections_count += 1

            chronology.append({
                "sequence_number": e.sequence_number,
                "event_type": e.event_type,
                "provider": e.provider,
                "timestamp_utc": e.timestamp_utc,
                "payload_hash": e.payload_hash,
                "sha256_hash": e.sha256_hash
            })

        return {
            "external_event_id": external_event_id,
            "total_events": len(events_sorted),
            "providers_observed": sorted(list(providers_observed)),
            "latest_status_by_provider": latest_status_by_provider,
            "latest_scores_by_provider": latest_scores_by_provider,
            "is_finalized": is_finalized,
            "conflicts_detected": conflicts_detected,
            "corrections_count": corrections_count,
            "event_chronology": chronology
        }


class HistoricalInformationIntegrityAnalyzer:
    """Read-only scientific integrity analyzer enforcing historical information availability boundaries (RCE-003.0)."""

    def __init__(self, ledger: SportsLongitudinalLedger):
        self.ledger = ledger

    def analyze_availability_at_timestamp(
        self,
        research_timestamp_utc: str,
        external_event_id: Optional[str] = None
    ) -> ObservationAvailabilitySnapshot:
        if not research_timestamp_utc:
            raise ValueError("RESEARCH_TIMESTAMP_REQUIRED: Historical availability analysis requires an explicit research timestamp T.")

        try:
            target_t = parse_iso_utc(research_timestamp_utc)
        except Exception:
            raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Invalid ISO 8601 research timestamp '{research_timestamp_utc}'.")

        stream = SportsObservationEventStream(self.ledger)
        all_events = self.ledger.observation_event_stream
        if external_event_id:
            all_events = [e for e in all_events if e.external_event_id == external_event_id]

        all_temporal = self.ledger.temporal_observations
        if external_event_id:
            all_temporal = [t for t in all_temporal if t.external_event_id == external_event_id]

        available = []
        excluded = []
        leakage_detected = False
        breakdown = {
            ObservationAvailabilityClassification.AVAILABLE.value: 0,
            ObservationAvailabilityClassification.AVAILABLE_AFTER_RESEARCH_TIME.value: 0,
            ObservationAvailabilityClassification.LATE_OBSERVATION.value: 0,
            ObservationAvailabilityClassification.CORRECTION_NOT_AVAILABLE_AT_T.value: 0,
            ObservationAvailabilityClassification.POST_TIMESTAMP_LEAKAGE.value: 0,
            ObservationAvailabilityClassification.FAIL_CLOSED_AMBIGUOUS_TIMING.value: 0,
        }

        # Analyze stream events
        for evt in all_events:
            ts_str = evt.timestamp_utc
            if not ts_str:
                classification = ObservationAvailabilityClassification.FAIL_CLOSED_AMBIGUOUS_TIMING.value
                excluded.append({"event_stream_id": evt.event_stream_id, "classification": classification, "reason": "Missing timestamp"})
                breakdown[classification] += 1
                continue

            try:
                ingest_dt = parse_iso_utc(ts_str)
            except Exception:
                classification = ObservationAvailabilityClassification.FAIL_CLOSED_AMBIGUOUS_TIMING.value
                excluded.append({"event_stream_id": evt.event_stream_id, "classification": classification, "reason": "Unparseable timestamp"})
                breakdown[classification] += 1
                continue

            if ingest_dt <= target_t:
                classification = ObservationAvailabilityClassification.AVAILABLE.value
                available.append({"event_stream_id": evt.event_stream_id, "event_type": evt.event_type, "timestamp_utc": ts_str, "classification": classification})
                breakdown[classification] += 1
            else:
                leakage_detected = True
                classification = ObservationAvailabilityClassification.POST_TIMESTAMP_LEAKAGE.value
                excluded.append({"event_stream_id": evt.event_stream_id, "event_type": evt.event_type, "timestamp_utc": ts_str, "classification": classification})
                breakdown[classification] += 1

        # Analyze temporal observation records
        for temp in all_temporal:
            ret_str = temp.retrieval_timestamp_utc
            obs_str = temp.observation_timestamp_utc

            if not ret_str:
                classification = ObservationAvailabilityClassification.FAIL_CLOSED_AMBIGUOUS_TIMING.value
                excluded.append({"temporal_id": temp.temporal_id, "classification": classification, "reason": "Missing retrieval timestamp"})
                breakdown[classification] += 1
                continue

            try:
                ret_dt = parse_iso_utc(ret_str)
            except Exception:
                classification = ObservationAvailabilityClassification.FAIL_CLOSED_AMBIGUOUS_TIMING.value
                excluded.append({"temporal_id": temp.temporal_id, "classification": classification, "reason": "Unparseable retrieval timestamp"})
                breakdown[classification] += 1
                continue

            if ret_dt <= target_t:
                classification = ObservationAvailabilityClassification.AVAILABLE.value
                available.append({"temporal_id": temp.temporal_id, "provider": temp.provider, "retrieval_timestamp_utc": ret_str, "classification": classification})
                breakdown[classification] += 1
            else:
                leakage_detected = True
                if temp.correction_detected:
                    classification = ObservationAvailabilityClassification.CORRECTION_NOT_AVAILABLE_AT_T.value
                else:
                    classification = ObservationAvailabilityClassification.LATE_OBSERVATION.value if obs_str and parse_iso_utc(obs_str) <= target_t else ObservationAvailabilityClassification.AVAILABLE_AFTER_RESEARCH_TIME.value

                excluded.append({"temporal_id": temp.temporal_id, "provider": temp.provider, "retrieval_timestamp_utc": ret_str, "classification": classification})
                breakdown[classification] += 1

        total_analyzed = len(available) + len(excluded)
        snap_id = f"snap_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        return ObservationAvailabilitySnapshot(
            snapshot_id=snap_id,
            research_timestamp_utc=research_timestamp_utc,
            total_observations_analyzed=total_analyzed,
            available_observations=available,
            excluded_observations=excluded,
            leakage_detected=leakage_detected,
            classification_breakdown=breakdown
        )

    def create_research_snapshot(
        self,
        research_timestamp_utc: str,
        external_event_id: Optional[str] = None
    ) -> tuple[HistoricalResearchSnapshot, ResearchIntegrityReceipt]:
        """Reconstructs point-in-time observable state at research timestamp T and generates leakage receipt (RCE-003.1)."""
        if not research_timestamp_utc:
            raise ValueError("RESEARCH_TIMESTAMP_REQUIRED: Historical research snapshot requires an explicit research timestamp T.")

        try:
            target_t = parse_iso_utc(research_timestamp_utc)
        except Exception:
            raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Invalid ISO 8601 research timestamp '{research_timestamp_utc}'.")

        # Gather observation event stream items
        all_events = self.ledger.observation_event_stream
        if external_event_id:
            all_events = [e for e in all_events if e.external_event_id == external_event_id]

        # Gather temporal observation records
        all_temporal = self.ledger.temporal_observations
        if external_event_id:
            all_temporal = [t for t in all_temporal if t.external_event_id == external_event_id]

        included_refs = []
        excluded_refs = []
        event_ids_set = set()
        provider_events_as_of_t: Dict[str, Dict[str, Any]] = {}
        conflict_refs = []
        leakage_detected = False

        # Sort all observation events deterministically by timestamp, then stream ID
        sorted_events = sorted(
            all_events,
            key=lambda x: (x.timestamp_utc or "", x.event_stream_id)
        )

        for evt in sorted_events:
            ts_str = evt.timestamp_utc
            if not ts_str:
                raise ValueError("FAIL_CLOSED_AMBIGUOUS_TIMING: Missing timestamp on event stream item.")

            try:
                ingest_dt = parse_iso_utc(ts_str)
            except Exception:
                raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Unparseable timestamp '{ts_str}' on event stream item.")

            ref_id = evt.event_stream_id
            event_ids_set.add(evt.external_event_id)

            if ingest_dt <= target_t:
                included_refs.append(ref_id)
                key = f"{evt.provider}::{evt.external_event_id}"
                # Latest event as of T overwrites earlier events for that provider/event
                provider_events_as_of_t[key] = {
                    "provider": evt.provider,
                    "external_event_id": evt.external_event_id,
                    "status": evt.details.get("status", "UNKNOWN"),
                    "home_score": evt.details.get("home_score"),
                    "away_score": evt.details.get("away_score"),
                    "is_final": evt.details.get("is_final") or (evt.event_type == SportsObservationEventType.OBS_FINALIZED.value),
                    "payload_hash": evt.payload_hash,
                    "as_of_timestamp_utc": ts_str,
                    "last_ref_id": ref_id
                }
            else:
                excluded_refs.append(ref_id)
                leakage_detected = True

        # Process temporal observation records
        sorted_temporal = sorted(
            all_temporal,
            key=lambda x: (x.retrieval_timestamp_utc or "", x.temporal_id)
        )

        for temp in sorted_temporal:
            ret_str = temp.retrieval_timestamp_utc
            if not ret_str:
                raise ValueError("FAIL_CLOSED_AMBIGUOUS_TIMING: Missing retrieval timestamp on temporal record.")

            try:
                ret_dt = parse_iso_utc(ret_str)
            except Exception:
                raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Unparseable retrieval timestamp '{ret_str}' on temporal record.")

            ref_id = temp.temporal_id
            event_ids_set.add(temp.external_event_id)

            if ret_dt <= target_t:
                included_refs.append(ref_id)
                key = f"{temp.provider}::{temp.external_event_id}"
                # If no stream event exists or temporal observation is newer, update provider event state as of T
                existing = provider_events_as_of_t.get(key)
                if not existing or parse_iso_utc(ret_str) >= parse_iso_utc(existing["as_of_timestamp_utc"]):
                    provider_events_as_of_t[key] = {
                        "provider": temp.provider,
                        "external_event_id": temp.external_event_id,
                        "status": temp.provider_status,
                        "home_score": None if not existing else existing.get("home_score"),
                        "away_score": None if not existing else existing.get("away_score"),
                        "is_final": temp.finality_state,
                        "payload_hash": temp.source_payload_hash,
                        "as_of_timestamp_utc": ret_str,
                        "last_ref_id": ref_id
                    }
                if temp.temporal_classification == ObservationTemporalClassification.TEMPORAL_CONFLICTED.value:
                    conflict_refs.append(ref_id)
            else:
                excluded_refs.append(ref_id)
                leakage_detected = True

        # Evaluate multi-provider consensus / conflict as of T
        providers_state: Dict[str, Dict[str, Any]] = {}
        event_status_map: Dict[str, List[Dict[str, Any]]] = {}

        for key, p_data in sorted(provider_events_as_of_t.items()):
            ext_id = p_data["external_event_id"]
            providers_state[key] = p_data
            event_status_map.setdefault(ext_id, []).append(p_data)

        # Check for provider conflicts as of T
        for ext_id, p_list in event_status_map.items():
            if len(p_list) > 1:
                statuses = {p["status"] for p in p_list}
                finalities = {p["is_final"] for p in p_list}
                home_scores = {p["home_score"] for p in p_list if p.get("home_score") is not None}
                away_scores = {p["away_score"] for p in p_list if p.get("away_score") is not None}
                if len(statuses) > 1 or len(finalities) > 1 or len(home_scores) > 1 or len(away_scores) > 1:
                    conflict_refs.append(f"conflict_as_of_{ext_id}")

        effective_state = {
            "research_timestamp_utc": research_timestamp_utc,
            "external_events_covered": sorted(list(event_ids_set)),
            "providers_state": providers_state,
            "provider_count": len(providers_state)
        }

        # Deterministic snapshot ID based on research timestamp and external event ID
        event_suffix = f"_{external_event_id}" if external_event_id else ""
        ts_slug = research_timestamp_utc.replace(":", "").replace("-", "").replace("+", "_").replace(".", "_")
        snapshot_id = f"snap_research_{ts_slug}{event_suffix}"

        snapshot = HistoricalResearchSnapshot(
            snapshot_id=snapshot_id,
            research_timestamp_utc=research_timestamp_utc,
            event_identities=sorted(list(event_ids_set)),
            included_observation_references=sorted(included_refs),
            excluded_post_timestamp_references=sorted(excluded_refs),
            effective_observation_state=effective_state,
            source_conflict_references=sorted(list(set(conflict_refs)))
        )

        receipt_id = f"rcpt_leakage_{ts_slug}{event_suffix}"
        if leakage_detected:
            integrity_status = "POST_TIMESTAMP_INFORMATION_DETECTED"
            reason = f"Excluded {len(excluded_refs)} observation references with availability timestamp > T ({research_timestamp_utc})."
        else:
            integrity_status = "RESEARCH_TIME_CLEAN"
            reason = f"All {len(included_refs)} analyzed observation references were available at or before T ({research_timestamp_utc})."

        receipt = ResearchIntegrityReceipt(
            receipt_id=receipt_id,
            snapshot_id=snapshot.snapshot_id,
            research_timestamp_utc=research_timestamp_utc,
            observed_reference_set=snapshot.included_observation_references,
            post_timestamp_reference_set=snapshot.excluded_post_timestamp_references,
            excluded_count=len(excluded_refs),
            integrity_status=integrity_status,
            reason=reason,
            snapshot_hash=snapshot.snapshot_hash
        )

        return snapshot, receipt
