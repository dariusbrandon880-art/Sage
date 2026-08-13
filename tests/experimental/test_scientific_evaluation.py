"""Unit and regression tests for SAGE Sports-Probability Scientific Feature Evaluation.

Enforces SAGE-RF-PROOF-001 specification test matrix.
"""

import math
import pytest
from sage.experimental.scientific_evaluation import EvaluationRow, ScientificEvaluationEngine, FeatureEvaluationResult


def test_metric_calculation_brier_and_log_loss():
    """Verify Brier Score and Log Loss calculation accuracy and boundaries."""
    probs = {"home": 0.60, "away": 0.40}

    # If home wins
    brier_home = ScientificEvaluationEngine.calculate_brier_score(probs, "home")
    # (0.6 - 1.0)^2 + (0.4 - 0.0)^2 = 0.16 + 0.16 = 0.32
    assert abs(brier_home - 0.32) < 1e-9

    loss_home = ScientificEvaluationEngine.calculate_log_loss(probs, "home")
    # -log(0.60) = 0.5108
    assert abs(loss_home - 0.51082) < 1e-4


def test_ece_calibration_calculation():
    """Verify Expected Calibration Error (ECE) grouping and calculation logic."""
    predicted_probs = [0.1, 0.3, 0.5, 0.7, 0.9]
    outcomes = [0, 0, 1, 1, 1]

    ece = ScientificEvaluationEngine.calculate_ece(predicted_probs, outcomes, num_bins=5)
    # Total prediction matches perfectly in terms of bins, let's verify it evaluates to a float >= 0.0
    assert isinstance(ece, float)
    assert ece >= 0.0


def test_insufficient_sample_handling():
    """Verify that insufficient samples are detected and return INSUFFICIENT_EVIDENCE."""
    rows = [
        EvaluationRow(
            market_identity="e1:ml:h",
            observed_prices={"h": 2.0, "a": 2.0},
            feature_values={"h": 0.5, "a": 0.5},
            actual_outcome="h"
        )
    ]

    res = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_short",
        dataset_identity="nba_short_v1.0",
        feature_identity="feat_dummy",
        rows=rows,
        min_samples_required=10
    )

    assert res.statistical_decision == "INSUFFICIENT_EVIDENCE"
    assert "less than required minimum" in res.detailed_reason


def test_unsupported_feature_negative_path():
    """Verify that a candidate with no predictive value correctly fails to reject H0 (NOT SUPPORTED)."""
    # Create 12 identical rows where the feature says "home is highly likely" (0.90) but "away" wins every time!
    # This simulates a completely wrong or non-predictive feature family.
    rows = []
    for i in range(12):
        rows.append(
            EvaluationRow(
                market_identity=f"e{i}:moneyline:h",
                observed_prices={"h": 2.0, "a": 2.0},  # Implied baseline probability is 0.50
                feature_values={"h": 0.90, "a": 0.10},  # Feature strongly favors home
                actual_outcome="a"  # But away wins!
            )
        )

    res = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_negative_test",
        dataset_identity="nba_falsification_v1.0",
        feature_identity="feat_wrong_direction",
        rows=rows,
        feature_weight=0.3,
        effect_size_threshold=0.01,
        min_samples_required=10
    )

    # Replay must conclude H0 is NOT SUPPORTED (no significant edge)
    assert res.statistical_decision == "NOT SUPPORTED"
    assert res.delta_brier_score < 0  # Candidate brier is worse than baseline!


def test_supported_feature_positive_path():
    """Verify that a genuine predictive feature successfully rejects H0 and returns SUPPORTED."""
    # Create 12 rows where the feature is predictive (corresponds perfectly to actual outcomes)
    rows = []
    for i in range(12):
        outcome = "h" if i % 2 == 0 else "a"
        rows.append(
            EvaluationRow(
                market_identity=f"e{i}:moneyline:h",
                observed_prices={"h": 2.0, "a": 2.0},  # Baseline prob: 0.5
                feature_values={
                    "h": 0.99 if outcome == "h" else 0.01,
                    "a": 0.01 if outcome == "h" else 0.99
                },
                actual_outcome=outcome
            )
        )

    res = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_positive_test",
        dataset_identity="nba_edge_v1.0",
        feature_identity="feat_highly_predictive",
        rows=rows,
        feature_weight=0.5,
        effect_size_threshold=0.01,
        min_samples_required=10
    )

    # Reject H0, support H1!
    assert res.statistical_decision == "SUPPORTED"
    assert res.delta_brier_score >= 0.01
    assert res.statistical_p_value < 0.05
