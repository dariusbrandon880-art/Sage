"""SAGE Sports-Probability Scientific Research - Scientific Feature Evaluation.

Implements the SAGE-RF-PROOF-001 specification:
Establishes the smallest executable scientific evaluation substrate capable of
determining whether a candidate feature contains incremental information beyond
the market baseline.
"""

import math
import os
import json
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field

from sage.experimental.market_baseline import MarketBaselineEngine


class EvaluationRow(BaseModel):
    """Represent a single historical sportsbook observation point-in-time state and actual outcome."""
    market_identity: str = Field(..., description="Unique isolated market key (e.g. event:market:selection)")
    observed_prices: Dict[str, float] = Field(..., description="Observed decimal prices per selection")
    feature_values: Dict[str, float] = Field(..., description="Candidate feature signal values per selection (e.g., normalized probability adjustment)")
    actual_outcome: str = Field(..., description="The actual winning selection (e.g., home or away)")


class FeatureEvaluationResult(BaseModel):
    """Rigorous scientific result output for a candidate feature evaluation."""
    experiment_id: str
    dataset_identity: str
    feature_identity: str
    hypothesis_version: str = "H0_vs_H1_v1.0"
    sample_count: int
    baseline_brier_score: float
    candidate_brier_score: float
    baseline_log_loss: float
    candidate_log_loss: float
    delta_brier_score: float
    delta_log_loss: float
    baseline_ece: float
    candidate_ece: float
    statistical_p_value: float
    effect_size_threshold: float
    statistical_decision: str  # "SUPPORTED", "NOT SUPPORTED", or "INSUFFICIENT_EVIDENCE"
    detailed_reason: str


class ScientificEvaluationEngine:
    """Scientific engine to test, compare, and falsify feature candidate hypotheses against market baselines."""

    @staticmethod
    def calculate_brier_score(probabilities: Dict[str, float], actual_outcome: str) -> float:
        """Computes the Brier Score for a single prediction set and actual outcome."""
        score = 0.0
        for sel, prob in probabilities.items():
            y = 1.0 if sel == actual_outcome else 0.0
            score += math.pow(prob - y, 2)
        return score

    @staticmethod
    def calculate_log_loss(probabilities: Dict[str, float], actual_outcome: str) -> float:
        """Computes the Log Loss for a single prediction set and actual outcome."""
        prob = probabilities.get(actual_outcome, 1e-15)
        prob = max(1e-15, min(1.0 - 1e-15, prob))
        return -math.log(prob)

    @classmethod
    def calculate_ece(cls, predicted_probs: List[float], outcomes: List[int], num_bins: int = 5) -> float:
        """Computes Expected Calibration Error (ECE) across predictions and actual outcomes."""
        if not predicted_probs:
            return 0.0

        bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
        ece = 0.0
        n = len(predicted_probs)

        for i in range(num_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            # Find indices in current bin
            bin_indices = [
                idx for idx, p in enumerate(predicted_probs)
                if bin_lower <= p < bin_upper or (i == num_bins - 1 and p == bin_upper)
            ]

            if not bin_indices:
                continue

            bin_size = len(bin_indices)
            bin_predicted = [predicted_probs[idx] for idx in bin_indices]
            bin_actual = [outcomes[idx] for idx in bin_indices]

            avg_confidence = sum(bin_predicted) / bin_size
            avg_accuracy = sum(bin_actual) / bin_size

            ece += (bin_size / n) * abs(avg_confidence - avg_accuracy)

        return ece

    @classmethod
    def evaluate_feature(
        cls,
        experiment_id: str,
        dataset_identity: str,
        feature_identity: str,
        rows: List[EvaluationRow],
        feature_weight: float = 0.3,
        effect_size_threshold: float = 0.01,
        min_samples_required: int = 10
    ) -> FeatureEvaluationResult:
        """Tests the candidate feature's H0 hypothesis against the de-vigged market baseline."""
        sample_count = len(rows)

        # 1. Reject if sample count is insufficient
        if sample_count < min_samples_required:
            return FeatureEvaluationResult(
                experiment_id=experiment_id,
                dataset_identity=dataset_identity,
                feature_identity=feature_identity,
                sample_count=sample_count,
                baseline_brier_score=0.0,
                candidate_brier_score=0.0,
                baseline_log_loss=0.0,
                candidate_log_loss=0.0,
                delta_brier_score=0.0,
                delta_log_loss=0.0,
                baseline_ece=0.0,
                candidate_ece=0.0,
                statistical_p_value=1.0,
                effect_size_threshold=effect_size_threshold,
                statistical_decision="INSUFFICIENT_EVIDENCE",
                detailed_reason=f"Sample count {sample_count} is less than required minimum {min_samples_required}."
            )

        # 2. Iterate row-by-row and compute metrics
        baseline_briers = []
        candidate_briers = []
        baseline_log_losses = []
        candidate_log_losses = []

        # For ECE
        baseline_all_probs = []
        candidate_all_probs = []
        all_outcomes = []

        for row in rows:
            # Reconstruct baseline probabilities from RF-DEVIG-001 (Power Method)
            try:
                base_probs, _ = MarketBaselineEngine.devig_power_method(row.observed_prices)
            except Exception:
                # Fallback to proportional if power fails/arbitrage occurs
                base_probs, _ = MarketBaselineEngine.devig_proportional(row.observed_prices)

            # Reconstruct candidate probabilities combining baseline and feature
            candidate_probs = {}
            for sel in row.observed_prices:
                p_base = base_probs.get(sel, 0.0)
                feat_val = row.feature_values.get(sel, 0.0)
                candidate_probs[sel] = ((1.0 - feature_weight) * p_base) + (feature_weight * feat_val)

            # Normalize candidate probabilities
            total_cand_p = sum(candidate_probs.values())
            if total_cand_p > 0:
                for sel in candidate_probs:
                    candidate_probs[sel] /= total_cand_p

            # Brier and Log Loss row-by-row scores
            base_brier = cls.calculate_brier_score(base_probs, row.actual_outcome)
            cand_brier = cls.calculate_brier_score(candidate_probs, row.actual_outcome)
            base_loss = cls.calculate_log_loss(base_probs, row.actual_outcome)
            cand_loss = cls.calculate_log_loss(candidate_probs, row.actual_outcome)

            baseline_briers.append(base_brier)
            candidate_briers.append(cand_brier)
            baseline_log_losses.append(base_loss)
            candidate_log_losses.append(cand_loss)

            for sel in row.observed_prices:
                baseline_all_probs.append(base_probs.get(sel, 0.0))
                candidate_all_probs.append(candidate_probs.get(sel, 0.0))
                all_outcomes.append(1 if sel == row.actual_outcome else 0)

        # Average metrics
        avg_base_brier = sum(baseline_briers) / sample_count
        avg_cand_brier = sum(candidate_briers) / sample_count
        avg_base_loss = sum(baseline_log_losses) / sample_count
        avg_cand_loss = sum(candidate_log_losses) / sample_count

        delta_brier = avg_base_brier - avg_cand_brier
        delta_loss = avg_base_loss - avg_cand_loss

        # Calculate ECE
        base_ece = cls.calculate_ece(baseline_all_probs, all_outcomes)
        cand_ece = cls.calculate_ece(candidate_all_probs, all_outcomes)

        # 3. Paired T-Test to compute statistical p-value over Brier difference
        diffs = [b - c for b, c in zip(baseline_briers, candidate_briers)]
        mean_diff = sum(diffs) / sample_count
        var_diff = sum(math.pow(d - mean_diff, 2) for d in diffs) / (sample_count - 1) if sample_count > 1 else 0.0
        std_err = math.sqrt(var_diff / sample_count) if var_diff > 0 else 0.0

        if std_err > 0:
            t_stat = mean_diff / std_err
            p_val = 0.5 * (1.0 - math.erf(t_stat / math.sqrt(2.0)))
        else:
            p_val = 0.0 if mean_diff > 0 else 1.0

        # 4. Enforce strict scientific boundaries for statistical decision
        if delta_brier >= effect_size_threshold and p_val < 0.05:
            decision = "SUPPORTED"
            reason = f"Candidate feature significantly outperforms baseline. Delta Brier: {delta_brier:.4f} >= threshold {effect_size_threshold:.4f} (p-value: {p_val:.4f}). H0 rejected."
        else:
            decision = "NOT SUPPORTED"
            if delta_brier <= 0:
                reason = f"Candidate feature underperforms or matches baseline. Delta Brier: {delta_brier:.4f} <= 0. H0 stands."
            elif delta_brier < effect_size_threshold:
                reason = f"Candidate feature improvement is too small. Delta Brier: {delta_brier:.4f} < practical threshold {effect_size_threshold:.4f}. H0 stands."
            else:
                reason = f"Candidate feature improvement is not statistically significant (p-value: {p_val:.4f}). H0 stands."

        return FeatureEvaluationResult(
            experiment_id=experiment_id,
            dataset_identity=dataset_identity,
            feature_identity=feature_identity,
            sample_count=sample_count,
            baseline_brier_score=avg_base_brier,
            candidate_brier_score=avg_cand_brier,
            baseline_log_loss=avg_base_loss,
            candidate_log_loss=avg_cand_loss,
            delta_brier_score=delta_brier,
            delta_log_loss=delta_loss,
            baseline_ece=base_ece,
            candidate_ece=cand_ece,
            statistical_p_value=p_val,
            effect_size_threshold=effect_size_threshold,
            statistical_decision=decision,
            detailed_reason=reason
        )
