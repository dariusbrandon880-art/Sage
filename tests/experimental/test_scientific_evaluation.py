"""Unit and regression tests for SAGE Sports-Probability Scientific Feature Evaluation.

Enforces SAGE-RF-PROOF-002 specification test matrix.
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
    assert isinstance(ece, float)
    assert ece >= 0.0


def test_deterministic_partitioning():
    """Verify that train/OOS partitioning is deterministic and repeatable (Locked OOS contract)."""
    rows = []
    for i in range(10):
        rows.append(
            EvaluationRow(
                market_identity=f"nba_{i}:ml:h",
                observed_prices={"h": 1.90, "a": 1.90},
                feature_values={"h": 0.5, "a": 0.5},
                actual_outcome="h" if i % 2 == 0 else "a"
            )
        )

    train1, oos1 = ScientificEvaluationEngine.partition_train_oos(rows, oos_split=0.3)
    train2, oos2 = ScientificEvaluationEngine.partition_train_oos(rows, oos_split=0.3)

    assert len(train1) == 7
    assert len(oos1) == 3

    assert [r.market_identity for r in train1] == [r.market_identity for r in train2]
    assert [r.market_identity for r in oos1] == [r.market_identity for r in oos2]


def test_oos_insufficient_sample():
    """Verify that insufficient samples in the locked OOS set return INSUFFICIENT_EVIDENCE."""
    rows = []
    for i in range(10):
        rows.append(
            EvaluationRow(
                market_identity=f"nba_{i}:ml:h",
                observed_prices={"h": 1.90, "a": 1.90},
                feature_values={"h": 0.5, "a": 0.5},
                actual_outcome="h"
            )
        )

    res = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_insufficient",
        dataset_identity="nba_short",
        feature_identity="feat_test",
        rows=rows,
        min_samples_required=5,
        oos_split=0.1
    )

    assert res.statistical_decision == "INSUFFICIENT_EVIDENCE"
    assert res.oos_sample_count == 1
    assert "less than required minimum" in res.detailed_reason


def test_leakage_detection_look_ahead():
    """Verify that perfect correlation (look-ahead outcome leakage) is detected and rejected."""
    rows = []
    for i in range(10):
        outcome = "h" if i % 2 == 0 else "a"
        rows.append(
            EvaluationRow(
                market_identity=f"nba_{i}:ml:h",
                observed_prices={"h": 2.0, "a": 2.0},
                feature_values={
                    "h": 1.0 if outcome == "h" else 0.0,
                    "a": 1.0 if outcome == "a" else 0.0
                },
                actual_outcome=outcome
            )
        )

    with pytest.raises(ValueError) as exc_info:
        ScientificEvaluationEngine.evaluate_feature(
            experiment_id="exp_leakage",
            dataset_identity="nba_leak",
            feature_identity="feat_leaked",
            rows=rows,
            min_samples_required=3,
            oos_split=0.5
        )
    assert "REJECTED / INVALID_EVALUATION" in str(exc_info.value)
    assert "leakage detected" in str(exc_info.value).lower()


def test_leakage_detection_simulated():
    """Verify simulated leakage parameter forces immediate fail-closed outcome."""
    rows = []
    for i in range(10):
        rows.append(
            EvaluationRow(
                market_identity=f"nba_{i}:ml:h",
                observed_prices={"h": 1.90, "a": 1.90},
                feature_values={"h": 0.5, "a": 0.5},
                actual_outcome="h"
            )
        )

    with pytest.raises(ValueError) as exc_info:
        ScientificEvaluationEngine.evaluate_feature(
            experiment_id="exp_leak_sim",
            dataset_identity="nba_leak_sim",
            feature_identity="feat_test",
            rows=rows,
            simulate_leakage=True
        )
    assert "REJECTED / INVALID_EVALUATION" in str(exc_info.value)


def test_decision_determinism():
    """Verify that evaluating the exact same inputs produces identical, reproducible results."""
    rows = []
    for i in range(15):
        outcome = "h" if i % 2 == 0 else "a"
        rows.append(
            EvaluationRow(
                market_identity=f"nba_det_{i}:ml:h",
                observed_prices={"h": 1.90, "a": 1.90},
                feature_values={
                    "h": 0.80 if outcome == "h" else 0.20,
                    "a": 0.20 if outcome == "h" else 0.80
                },
                actual_outcome=outcome
            )
        )

    res1 = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_det_1",
        dataset_identity="nba_det",
        feature_identity="feat_test",
        rows=rows,
        min_samples_required=5,
        oos_split=0.3
    )

    res2 = ScientificEvaluationEngine.evaluate_feature(
        experiment_id="exp_det_1",
        dataset_identity="nba_det",
        feature_identity="feat_test",
        rows=rows,
        min_samples_required=5,
        oos_split=0.3
    )

    assert res1.baseline_brier_score == res2.baseline_brier_score
    assert res1.candidate_brier_score == res2.candidate_brier_score
    assert res1.delta_brier_score == res2.delta_brier_score
    assert res1.statistical_decision == res2.statistical_decision
    assert res1.statistical_p_value == res2.statistical_p_value


def test_unsupported_feature_negative_path():
    """Verify that a candidate with no predictive value correctly fails to reject H0 (NOT SUPPORTED)."""
    rows = []
    for i in range(15):
        rows.append(
            EvaluationRow(
                market_identity=f"nba_neg_{i}:moneyline:h",
                observed_prices={"h": 2.0, "a": 2.0},
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
        min_samples_required=4,
        oos_split=0.3
    )

    assert res.statistical_decision == "NOT SUPPORTED"
    assert res.delta_brier_score < 0


def test_supported_feature_positive_path():
    """Verify that a genuine predictive feature successfully rejects H0 and returns SUPPORTED."""
    rows = []
    for i in range(20):
        outcome = "h" if i % 2 == 0 else "a"
        rows.append(
            EvaluationRow(
                market_identity=f"nba_pos_{i}:moneyline:h",
                observed_prices={"h": 2.0, "a": 2.0},
                feature_values={
                    "h": 0.85 if outcome == "h" else 0.15,
                    "a": 0.15 if outcome == "h" else 0.85
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
        min_samples_required=5,
        oos_split=0.3
    )

    assert res.statistical_decision == "SUPPORTED"
    assert res.delta_brier_score >= 0.01
    assert res.statistical_p_value < 0.05
