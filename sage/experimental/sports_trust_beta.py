"""SAGE Sports Trust Beta — Shadow Prediction Trust Flight Substrate.

Provides a bounded, paper/shadow trust laboratory cycle:
OBSERVE -> LOCK -> PREDICT -> RESOLVE -> SCORE -> LEARN -> REPORT.

Enforces:
- Strict pre-event temporal locking (lock_timestamp_utc < event_start_time_utc).
- Zero real-money execution, wagering, bookmaker account access, or bet placement (fail-closed).
- Immutable SHA-256 pre-event prediction lock receipts.
- Explicit abstention and unavailable-data handling without forced guessing.
- Separate append-only outcome, scoring, and learning recordkeeping.
- Brier score calibration, accuracy, and mean absolute calibration error tracking.
- Falsification of contaminated or backdated evidence.
"""

json_import = True
import json
import hashlib
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    SportsOutcomeRecord,
    SportsScoreRecord,
    SportsLearningRecord,
    SportsLongitudinalLedger,
    parse_iso_utc,
    calculate_brier_score,
)


@dataclass
class SportsTrustShadowPrediction:
    """Pre-event locked shadow prediction for trust evaluation."""

    prediction_id: str
    cycle_id: str
    event_observation: RealSportsEventObservation
    selected_prediction: str
    odds_at_lock: str
    implied_probability: float | str
    model_predicted_probability: Optional[float]
    lock_timestamp_utc: str
    model_state_rationale: str
    is_abstention: bool = False
    abstention_reason: Optional[str] = None
    wagering_allowed: bool = False  # MUST ALWAYS BE FALSE
    classification: str = "SPORTS TRUST BETA — SHADOW PREDICTION"
    sha256_receipt_hash: str = ""

    def __post_init__(self):
        # Enforce strict shadow boundary: NO real-money wagering or execution allowed
        if self.wagering_allowed:
            raise ValueError(
                "SHADOW_BOUNDARY_VIOLATION: Wagering or real-money execution is strictly forbidden in Sports Trust Beta."
            )

        # Enforce Temporal Lock invariant: lock_timestamp_utc MUST BE strictly less than event_start_time_utc
        lock_dt = parse_iso_utc(self.lock_timestamp_utc)
        start_dt = parse_iso_utc(self.event_observation.event_start_time_utc)
        if lock_dt >= start_dt:
            raise ValueError(
                f"TEMPORAL_LOCK_VIOLATION: Lock timestamp {self.lock_timestamp_utc} "
                f"is at or after event start time {self.event_observation.event_start_time_utc}."
            )

        # Validate probability bounds if not abstaining
        if not self.is_abstention and self.model_predicted_probability is not None:
            if not (0.0 <= self.model_predicted_probability <= 1.0):
                raise ValueError(
                    f"INVALID_PROBABILITY: Predicted probability {self.model_predicted_probability} must be between 0.0 and 1.0."
                )

    def compute_sha256_hash(self) -> str:
        """Computes canonical SHA-256 digest covering all pre-event locked prediction fields."""
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
            "is_abstention": self.is_abstention,
            "abstention_reason": self.abstention_reason,
            "wagering_allowed": False,
            "classification": self.classification,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def lock_and_sign(self) -> str:
        self.sha256_receipt_hash = self.compute_sha256_hash()
        return self.sha256_receipt_hash


@dataclass
class SportsTrustResolution:
    """Outcome resolution record for a shadow prediction."""

    resolution_id: str
    prediction_id: str
    prediction_hash: str
    verification_timestamp_utc: str
    verification_source_name: str
    verification_source_url: str
    actual_home_score: Optional[int]
    actual_away_score: Optional[int]
    actual_result_text: str
    outcome_status: str  # WIN, LOSS, PUSH, VOID, UNAVAILABLE
    classification: str = "SPORTS TRUST BETA — RESOLUTION"
    resolution_receipt_hash: str = ""

    def __post_init__(self):
        valid_statuses = {"WIN", "LOSS", "PUSH", "VOID", "UNAVAILABLE"}
        if self.outcome_status not in valid_statuses:
            raise ValueError(f"INVALID_OUTCOME_STATUS: Outcome status '{self.outcome_status}' is not in {valid_statuses}.")

    def compute_sha256_hash(self) -> str:
        payload = {
            "resolution_id": self.resolution_id,
            "prediction_id": self.prediction_id,
            "prediction_hash": self.prediction_hash,
            "verification_timestamp_utc": self.verification_timestamp_utc,
            "verification_source_name": self.verification_source_name,
            "verification_source_url": self.verification_source_url,
            "actual_home_score": self.actual_home_score,
            "actual_away_score": self.actual_away_score,
            "actual_result_text": self.actual_result_text,
            "outcome_status": self.outcome_status,
            "classification": self.classification,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.resolution_receipt_hash = self.compute_sha256_hash()
        return self.resolution_receipt_hash


@dataclass
class SportsTrustScoreReport:
    """Calibration, accuracy, and abstention performance summary."""

    total_predictions: int
    resolved_count: int
    unresolved_count: int
    wins: int
    losses: int
    pushes: int
    voids: int
    unavailables: int
    abstentions: int
    hit_rate: float
    brier_score: Optional[float]
    mean_absolute_calibration_error: Optional[float]
    classification_breakdown: Dict[str, int] = field(default_factory=dict)


class SportsTrustBetaFlightEngine:
    """Engine executing the SAGE Sports Trust Beta shadow prediction trust flight."""

    def __init__(self, ledger: Optional[SportsLongitudinalLedger] = None, allow_real_wagering: bool = False):
        if allow_real_wagering:
            raise ValueError(
                "SHADOW_BOUNDARY_VIOLATION: Real-money wagering configuration is strictly prohibited."
            )
        self.ledger = ledger or SportsLongitudinalLedger()
        self.shadow_predictions: List[SportsTrustShadowPrediction] = []
        self._shadow_prediction_ids: set[str] = set()

    def create_shadow_prediction(
        self,
        prediction_id: str,
        cycle_id: str,
        event_observation: RealSportsEventObservation,
        selected_prediction: str,
        odds_at_lock: str,
        implied_probability: float | str,
        model_predicted_probability: Optional[float],
        lock_timestamp_utc: str,
        model_state_rationale: str,
        is_abstention: bool = False,
        abstention_reason: Optional[str] = None,
    ) -> SportsTrustShadowPrediction:
        """Constructs, validates, locks, and persists a shadow research prediction."""
        if prediction_id in self._shadow_prediction_ids:
            raise ValueError(f"DUPLICATE_PREDICTION_ID: Shadow prediction ID '{prediction_id}' already exists.")

        pred = SportsTrustShadowPrediction(
            prediction_id=prediction_id,
            cycle_id=cycle_id,
            event_observation=event_observation,
            selected_prediction=selected_prediction,
            odds_at_lock=odds_at_lock,
            implied_probability=implied_probability,
            model_predicted_probability=model_predicted_probability,
            lock_timestamp_utc=lock_timestamp_utc,
            model_state_rationale=model_state_rationale,
            is_abstention=is_abstention,
            abstention_reason=abstention_reason,
            wagering_allowed=False,
        )
        pred.lock_and_sign()

        self.shadow_predictions.append(pred)
        self._shadow_prediction_ids.add(prediction_id)

        # Convert to longitudinal ledger prediction for unified persistence and scoring
        prob = pred.model_predicted_probability if pred.model_predicted_probability is not None else 0.0
        implied_prob = pred.implied_probability if isinstance(pred.implied_probability, float) else 0.0

        long_pred = pred.event_observation
        from sage.experimental.sports_longitudinal import LockedResearchPrediction
        ledger_prediction = LockedResearchPrediction(
            prediction_id=pred.prediction_id,
            cycle_id=pred.cycle_id,
            event_observation=long_pred,
            selected_prediction=pred.selected_prediction,
            odds_at_lock=pred.odds_at_lock,
            implied_probability=implied_prob,
            model_predicted_probability=prob,
            lock_timestamp_utc=pred.lock_timestamp_utc,
            model_state_rationale=f"[TRUST_BETA|abstain={is_abstention}] {pred.model_state_rationale}",
            classification=pred.classification,
        )
        ledger_prediction.sha256_receipt_hash = pred.sha256_receipt_hash
        self.ledger.add_prediction(ledger_prediction)

        return pred

    def resolve_shadow_prediction(
        self,
        prediction_id: str,
        verification_source_name: str,
        verification_source_url: str,
        actual_home_score: Optional[int],
        actual_away_score: Optional[int],
        actual_result_text: str,
        outcome_status: str,
        verification_timestamp_utc: str,
    ) -> Tuple[SportsTrustResolution, SportsOutcomeRecord, Optional[SportsScoreRecord], Optional[SportsLearningRecord]]:
        """Resolves a shadow prediction, verifying hash integrity and emitting append-only ledger records."""
        shadow_pred = next((p for p in self.shadow_predictions if p.prediction_id == prediction_id), None)
        if not shadow_pred:
            raise KeyError(f"PREDICTION_NOT_FOUND: Shadow prediction '{prediction_id}' not found.")

        # Verify hash integrity
        computed_hash = shadow_pred.compute_sha256_hash()
        if shadow_pred.sha256_receipt_hash != computed_hash:
            raise ValueError(
                f"EVIDENCE_CONTAMINATION_DETECTED: Stored prediction hash {shadow_pred.sha256_receipt_hash} "
                f"does not match computed hash {computed_hash}."
            )

        resolution_id = f"res_trust_{prediction_id}"
        resolution = SportsTrustResolution(
            resolution_id=resolution_id,
            prediction_id=prediction_id,
            prediction_hash=shadow_pred.sha256_receipt_hash,
            verification_timestamp_utc=verification_timestamp_utc,
            verification_source_name=verification_source_name,
            verification_source_url=verification_source_url,
            actual_home_score=actual_home_score,
            actual_away_score=actual_away_score,
            actual_result_text=actual_result_text,
            outcome_status=outcome_status,
        )
        resolution.sign()

        # Map to longitudinal outcome record
        outcome = SportsOutcomeRecord(
            outcome_id=f"out_{prediction_id}",
            prediction_id=prediction_id,
            prediction_hash=shadow_pred.sha256_receipt_hash,
            verification_timestamp_utc=verification_timestamp_utc,
            verification_source_name=verification_source_name,
            verification_source_url=verification_source_url,
            actual_home_score=actual_home_score,
            actual_away_score=actual_away_score,
            actual_result_text=actual_result_text,
            outcome_status=outcome_status,
            classification="SPORTS TRUST BETA — OUTCOME",
        )
        outcome.sign()
        self.ledger.add_outcome(outcome)

        score = None
        learning = None

        # Calculate score and learning if resolved and not abstained
        if outcome_status in ["WIN", "LOSS"] and not shadow_pred.is_abstention and shadow_pred.model_predicted_probability is not None:
            prob = shadow_pred.model_predicted_probability
            actual_val = 1.0 if outcome_status == "WIN" else 0.0
            brier_contrib = (prob - actual_val) ** 2

            score = SportsScoreRecord(
                score_id=f"score_{prediction_id}",
                prediction_id=prediction_id,
                prediction_hash=shadow_pred.sha256_receipt_hash,
                outcome_id=outcome.outcome_id,
                score_timestamp_utc=verification_timestamp_utc,
                model_predicted_probability=prob,
                outcome_status=outcome_status,
                brier_score_contribution=brier_contrib,
                classification="SPORTS TRUST BETA — SCORING",
            )
            score.sign()
            self.ledger.add_score(score)

            fail_class = "PREDICTION_ERROR" if outcome_status == "LOSS" else None
            broken_assumption = (
                "Predicted probability exceeded outcome realization." if outcome_status == "LOSS" else None
            )
            lesson_text = (
                f"Shadow evaluation for {prediction_id}: outcome was {outcome_status} with predicted prob {prob:.4f}."
            )

            learning = SportsLearningRecord(
                learning_id=f"learn_{prediction_id}",
                prediction_id=prediction_id,
                prediction_hash=shadow_pred.sha256_receipt_hash,
                outcome_id=outcome.outcome_id,
                score_id=score.score_id,
                learning_timestamp_utc=verification_timestamp_utc,
                failure_classification=fail_class,
                model_assumption_broken=broken_assumption,
                lesson_recorded=lesson_text,
                classification="SPORTS TRUST BETA — LEARNING",
            )
            learning.sign()
            self.ledger.add_learning(learning)

        return resolution, outcome, score, learning

    def calculate_trust_metrics(self) -> SportsTrustScoreReport:
        """Calculates Brier score, mean absolute calibration error, hit rate, and abstention metrics."""
        total = len(self.shadow_predictions)
        abstentions = sum(1 for p in self.shadow_predictions if p.is_abstention)

        outcomes_by_id = {o.prediction_id: o for o in self.ledger.outcomes}

        wins = 0
        losses = 0
        pushes = 0
        voids = 0
        unavailables = 0
        resolved_count = 0

        calib_diffs = []
        brier_diffs = []

        for pred in self.shadow_predictions:
            out = outcomes_by_id.get(pred.prediction_id)
            if not out:
                continue

            status = out.outcome_status
            if status == "WIN":
                wins += 1
                resolved_count += 1
            elif status == "LOSS":
                losses += 1
                resolved_count += 1
            elif status == "PUSH":
                pushes += 1
            elif status == "VOID":
                voids += 1
            elif status == "UNAVAILABLE":
                unavailables += 1

            if status in ["WIN", "LOSS"] and not pred.is_abstention and pred.model_predicted_probability is not None:
                actual = 1.0 if status == "WIN" else 0.0
                prob = pred.model_predicted_probability
                calib_diffs.append(abs(prob - actual))
                brier_diffs.append((prob - actual) ** 2)

        unresolved = total - len(outcomes_by_id)
        hit_rate = (wins / resolved_count) if resolved_count > 0 else 0.0
        brier_score = (sum(brier_diffs) / len(brier_diffs)) if brier_diffs else None
        mace = (sum(calib_diffs) / len(calib_diffs)) if calib_diffs else None

        return SportsTrustScoreReport(
            total_predictions=total,
            resolved_count=resolved_count,
            unresolved_count=unresolved,
            wins=wins,
            losses=losses,
            pushes=pushes,
            voids=voids,
            unavailables=unavailables,
            abstentions=abstentions,
            hit_rate=hit_rate,
            brier_score=brier_score,
            mean_absolute_calibration_error=mace,
            classification_breakdown={
                "SPORTS TRUST BETA — SHADOW PREDICTION": total,
                "REAL-MONEY WAGERS": 0,
                "GAMBLING AUTOMATION": 0,
            },
        )

    def falsify_if_contaminated(self) -> Dict[str, Any]:
        """Falsifies evaluation and checks integrity across all shadow predictions and outcomes."""
        violations = []

        for pred in self.shadow_predictions:
            # Check prediction hash integrity
            if pred.sha256_receipt_hash != pred.compute_sha256_hash():
                violations.append({
                    "prediction_id": pred.prediction_id,
                    "violation": "HASH_MISMATCH",
                    "reason": "Stored prediction receipt hash does not match computed prediction hash."
                })

            # Check temporal lock integrity
            lock_dt = parse_iso_utc(pred.lock_timestamp_utc)
            start_dt = parse_iso_utc(pred.event_observation.event_start_time_utc)
            if lock_dt >= start_dt:
                violations.append({
                    "prediction_id": pred.prediction_id,
                    "violation": "TEMPORAL_LOCK_CONTAMINATION",
                    "reason": f"Lock timestamp {pred.lock_timestamp_utc} is at or after event start time {pred.event_observation.event_start_time_utc}."
                })

        # Check outcome references
        for out in self.ledger.outcomes:
            if out.outcome_receipt_hash != out.compute_sha256_hash():
                violations.append({
                    "outcome_id": out.outcome_id,
                    "violation": "OUTCOME_HASH_MISMATCH",
                    "reason": "Stored outcome receipt hash does not match computed outcome hash."
                })

        return {
            "is_clean": len(violations) == 0,
            "violations_count": len(violations),
            "violations": violations,
            "verdict": "VERIFIED_CLEAN" if len(violations) == 0 else "FALSIFIED_CONTAMINATED_EVIDENCE",
        }

    def generate_flight_summary(self) -> Dict[str, Any]:
        """Generates a complete, structured flight summary artifact for Sports Trust Beta."""
        metrics = self.calculate_trust_metrics()
        falsification = self.falsify_if_contaminated()

        return {
            "flight_type": "SPORTS TRUST BETA — SHADOW PREDICTION FLIGHT",
            "wagering_status": "NONE (PAPER / SHADOW RESEARCH ONLY)",
            "governance_compliance": {
                "shadow_boundary_enforced": True,
                "real_money_execution": False,
                "hindsight_leakage_prevented": falsification["is_clean"],
            },
            "metrics": asdict(metrics),
            "falsification_audit": falsification,
            "predictions_summary": [
                {
                    "prediction_id": p.prediction_id,
                    "event_id": p.event_observation.event_id,
                    "selection": p.selected_prediction,
                    "lock_timestamp": p.lock_timestamp_utc,
                    "predicted_prob": p.model_predicted_probability,
                    "is_abstention": p.is_abstention,
                    "receipt_hash": p.sha256_receipt_hash,
                }
                for p in self.shadow_predictions
            ],
            "ledger_summary": self.ledger.generate_summary_report(),
        }
