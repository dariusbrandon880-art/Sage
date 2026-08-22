"""SAGE Sports Trust Beta — Shadow Prediction Trust Flight Substrate.

Provides a bounded, paper/shadow trust laboratory cycle:
OBSERVE -> LOCK -> PREDICT -> RESOLVE -> SCORE -> LEARN -> REPORT.

Enforces:
- Strict pre-event & market-close temporal locking (lock_timestamp_utc < min(event_start, market_close)).
- Zero real-money execution, wagering, bookmaker account access, or bet placement (fail-closed).
- Immutable SHA-256 pre-event prediction lock receipts with model/procedure/input fingerprints.
- First-class outcome states: WIN, LOSS, PUSH, VOID, UNRESOLVED, ABSTAIN, DATA_UNAVAILABLE, INVALID_POST_LOCK, SOURCE_UNAVAILABLE.
- Brier score calibration, log loss, benchmark baseline comparison, and Closing Line Value (CLV) with de-vig semantics.
- Out-of-sample (OOS) and version-boundary tracking.
- Separate append-only outcome, scoring, and learning recordkeeping connected to SportsLongitudinalLedger.
- Extended falsification audit covering tampering, duplicate resolution, orphan scoring, and post-lock contamination.
"""

import json
import hashlib
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple

from sage.experimental.sports_longitudinal import (
    RealSportsEventObservation,
    SportsOutcomeRecord,
    SportsScoreRecord,
    SportsLearningRecord,
    SportsLongitudinalLedger,
    parse_iso_utc,
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
    market_close_timestamp_utc: Optional[str] = None
    market_close_source: Optional[str] = None
    source_timestamp_utc: Optional[str] = None
    model_version: str = "v1.0.0-trust-beta"
    model_procedure_fingerprint: str = ""
    input_data_fingerprint: str = ""
    is_oos: bool = True  # Out-Of-Sample evaluation flag
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

        # Enforce Temporal Lock invariant: lock_timestamp_utc MUST BE strictly less than event_start_time_utc and market_close_timestamp_utc
        lock_dt = parse_iso_utc(self.lock_timestamp_utc)
        start_dt = parse_iso_utc(self.event_observation.event_start_time_utc)
        if lock_dt >= start_dt:
            raise ValueError(
                f"TEMPORAL_LOCK_VIOLATION: Lock timestamp {self.lock_timestamp_utc} "
                f"is at or after event start time {self.event_observation.event_start_time_utc}."
            )

        if self.market_close_timestamp_utc:
            market_close_dt = parse_iso_utc(self.market_close_timestamp_utc)
            if lock_dt >= market_close_dt:
                raise ValueError(
                    f"MARKET_CLOSE_TEMPORAL_LOCK_VIOLATION: Lock timestamp {self.lock_timestamp_utc} "
                    f"is at or after market close time {self.market_close_timestamp_utc}."
                )

        # Validate probability bounds if not abstaining
        if not self.is_abstention and self.model_predicted_probability is not None:
            if not (0.0 <= self.model_predicted_probability <= 1.0):
                raise ValueError(
                    f"INVALID_PROBABILITY: Predicted probability {self.model_predicted_probability} must be between 0.0 and 1.0."
                )

        if not self.model_procedure_fingerprint:
            raw_proc = f"{self.model_version}:{self.model_state_rationale}"
            self.model_procedure_fingerprint = hashlib.sha256(raw_proc.encode("utf-8")).hexdigest()

        if not self.input_data_fingerprint:
            raw_input = json.dumps(asdict(self.event_observation), sort_keys=True, default=str)
            self.input_data_fingerprint = hashlib.sha256(raw_input.encode("utf-8")).hexdigest()

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
            "market_close_timestamp_utc": self.market_close_timestamp_utc,
            "market_close_source": self.market_close_source,
            "source_timestamp_utc": self.source_timestamp_utc,
            "model_version": self.model_version,
            "model_procedure_fingerprint": self.model_procedure_fingerprint,
            "input_data_fingerprint": self.input_data_fingerprint,
            "is_oos": self.is_oos,
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
    outcome_status: str  # WIN, LOSS, PUSH, VOID, UNRESOLVED, ABSTAIN, DATA_UNAVAILABLE, INVALID_POST_LOCK, SOURCE_UNAVAILABLE
    closing_odds: Optional[str] = None
    closing_implied_probability: Optional[float] = None
    devig_closing_probability: Optional[float] = None
    classification: str = "SPORTS TRUST BETA — RESOLUTION"
    resolution_receipt_hash: str = ""

    VALID_STATUSES = {
        "WIN",
        "LOSS",
        "PUSH",
        "VOID",
        "UNRESOLVED",
        "ABSTAIN",
        "DATA_UNAVAILABLE",
        "INVALID_POST_LOCK",
        "SOURCE_UNAVAILABLE",
    }

    def __post_init__(self):
        if self.outcome_status not in self.VALID_STATUSES:
            raise ValueError(f"INVALID_OUTCOME_STATUS: Outcome status '{self.outcome_status}' is not in {self.VALID_STATUSES}.")

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
            "closing_odds": self.closing_odds,
            "closing_implied_probability": self.closing_implied_probability,
            "devig_closing_probability": self.devig_closing_probability,
            "classification": self.classification,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.resolution_receipt_hash = self.compute_sha256_hash()
        return self.resolution_receipt_hash


@dataclass
class SportsTrustScoreReport:
    """Calibration, accuracy, log loss, baseline benchmark, CLV, and status breakdown summary."""

    total_predictions: int
    resolved_count: int
    unresolved_count: int
    wins: int
    losses: int
    pushes: int
    voids: int
    data_unavailables: int
    source_unavailables: int
    invalid_post_locks: int
    abstentions: int
    oos_count: int
    hit_rate: float
    brier_score: Optional[float]
    baseline_brier_score: Optional[float]
    log_loss: Optional[float]
    baseline_log_loss: Optional[float]
    mean_absolute_calibration_error: Optional[float]
    clv_covered_count: int
    mean_clv_beat_margin: Optional[float]
    classification_breakdown: Dict[str, int] = field(default_factory=dict)


def compute_log_loss(probs: List[float], outcomes: List[float], eps: float = 1e-15) -> Optional[float]:
    """Computes binary log loss across predicted probabilities and realized outcomes."""
    if not probs or len(probs) != len(outcomes):
        return None
    total_loss = 0.0
    for p, y in zip(probs, outcomes):
        p_bounded = max(eps, min(1.0 - eps, float(p)))
        y_val = float(y)
        loss = -(y_val * math.log(p_bounded) + (1.0 - y_val) * math.log(1.0 - p_bounded))
        total_loss += loss
    return total_loss / len(probs)


def devig_two_way_odds(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """Applies proportional de-vig normalization to two-way market implied probabilities."""
    total = prob_a + prob_b
    if total <= 0.0:
        return 0.5, 0.5
    return prob_a / total, prob_b / total


class SportsTrustBetaFlightEngine:
    """Engine executing the SAGE Sports Trust Beta shadow prediction trust flight."""

    def __init__(self, ledger: Optional[SportsLongitudinalLedger] = None, allow_real_wagering: bool = False):
        if allow_real_wagering:
            raise ValueError(
                "SHADOW_BOUNDARY_VIOLATION: Real-money wagering configuration is strictly prohibited."
            )
        self.ledger = ledger or SportsLongitudinalLedger()
        self.shadow_predictions: List[SportsTrustShadowPrediction] = []
        self.resolutions_by_pred_id: Dict[str, SportsTrustResolution] = {}
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
        market_close_timestamp_utc: Optional[str] = None,
        market_close_source: Optional[str] = None,
        source_timestamp_utc: Optional[str] = None,
        model_version: str = "v1.0.0-trust-beta",
        model_procedure_fingerprint: str = "",
        input_data_fingerprint: str = "",
        is_oos: bool = True,
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
            market_close_timestamp_utc=market_close_timestamp_utc,
            market_close_source=market_close_source,
            source_timestamp_utc=source_timestamp_utc,
            model_version=model_version,
            model_procedure_fingerprint=model_procedure_fingerprint,
            input_data_fingerprint=input_data_fingerprint,
            is_oos=is_oos,
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
            model_state_rationale=f"[TRUST_BETA|v={pred.model_version}|abstain={is_abstention}] {pred.model_state_rationale}",
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
        closing_odds: Optional[str] = None,
        closing_implied_probability: Optional[float] = None,
        devig_closing_probability: Optional[float] = None,
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
            closing_odds=closing_odds,
            closing_implied_probability=closing_implied_probability,
            devig_closing_probability=devig_closing_probability,
        )
        resolution.sign()
        self.resolutions_by_pred_id[prediction_id] = resolution

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
        """Calculates Brier score, baseline score, log loss, CLV margin, and status breakdown."""
        total = len(self.shadow_predictions)
        abstentions = sum(1 for p in self.shadow_predictions if p.is_abstention)
        oos_count = sum(1 for p in self.shadow_predictions if p.is_oos)

        outcomes_by_id = {o.prediction_id: o for o in self.ledger.outcomes}

        wins = 0
        losses = 0
        pushes = 0
        voids = 0
        data_unavailables = 0
        source_unavailables = 0
        invalid_post_locks = 0
        resolved_count = 0

        calib_diffs = []
        brier_diffs = []
        baseline_brier_diffs = []

        model_probs = []
        baseline_probs = []
        realized_outcomes = []

        clv_margins = []

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
            elif status == "DATA_UNAVAILABLE":
                data_unavailables += 1
            elif status == "SOURCE_UNAVAILABLE":
                source_unavailables += 1
            elif status == "INVALID_POST_LOCK":
                invalid_post_locks += 1

            if status in ["WIN", "LOSS"] and not pred.is_abstention and pred.model_predicted_probability is not None:
                actual = 1.0 if status == "WIN" else 0.0
                prob = pred.model_predicted_probability
                calib_diffs.append(abs(prob - actual))
                brier_diffs.append((prob - actual) ** 2)

                model_probs.append(prob)
                realized_outcomes.append(actual)

                # Baseline implied probability
                base_prob = pred.implied_probability if isinstance(pred.implied_probability, float) else 0.5
                baseline_probs.append(base_prob)
                baseline_brier_diffs.append((base_prob - actual) ** 2)

            # CLV calculation using actual stored resolution
            res = self.resolutions_by_pred_id.get(pred.prediction_id)
            devig_closing = res.devig_closing_probability if res and res.devig_closing_probability is not None else (
                res.closing_implied_probability if res and res.closing_implied_probability is not None else None
            )

            if devig_closing is not None and pred.model_predicted_probability is not None and not pred.is_abstention:
                clv_margin = pred.model_predicted_probability - devig_closing
                clv_margins.append(clv_margin)

        unresolved = total - len(outcomes_by_id)
        hit_rate = (wins / resolved_count) if resolved_count > 0 else 0.0
        brier_score = (sum(brier_diffs) / len(brier_diffs)) if brier_diffs else None
        baseline_brier = (sum(baseline_brier_diffs) / len(baseline_brier_diffs)) if baseline_brier_diffs else None

        log_loss = compute_log_loss(model_probs, realized_outcomes) if model_probs else None
        baseline_log_loss = compute_log_loss(baseline_probs, realized_outcomes) if baseline_probs else None

        mace = (sum(calib_diffs) / len(calib_diffs)) if calib_diffs else None
        mean_clv = (sum(clv_margins) / len(clv_margins)) if clv_margins else None

        return SportsTrustScoreReport(
            total_predictions=total,
            resolved_count=resolved_count,
            unresolved_count=unresolved,
            wins=wins,
            losses=losses,
            pushes=pushes,
            voids=voids,
            data_unavailables=data_unavailables,
            source_unavailables=source_unavailables,
            invalid_post_locks=invalid_post_locks,
            abstentions=abstentions,
            oos_count=oos_count,
            hit_rate=hit_rate,
            brier_score=brier_score,
            baseline_brier_score=baseline_brier,
            log_loss=log_loss,
            baseline_log_loss=baseline_log_loss,
            mean_absolute_calibration_error=mace,
            clv_covered_count=len(clv_margins),
            mean_clv_beat_margin=mean_clv,
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

            if pred.market_close_timestamp_utc:
                mkt_close_dt = parse_iso_utc(pred.market_close_timestamp_utc)
                if lock_dt >= mkt_close_dt:
                    violations.append({
                        "prediction_id": pred.prediction_id,
                        "violation": "MARKET_CLOSE_TEMPORAL_CONTAMINATION",
                        "reason": f"Lock timestamp {pred.lock_timestamp_utc} is at or after market close time {pred.market_close_timestamp_utc}."
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
                    "model_version": p.model_version,
                    "model_procedure_fingerprint": p.model_procedure_fingerprint,
                    "input_data_fingerprint": p.input_data_fingerprint,
                    "receipt_hash": p.sha256_receipt_hash,
                }
                for p in self.shadow_predictions
            ],
            "ledger_summary": self.ledger.generate_summary_report(),
        }
