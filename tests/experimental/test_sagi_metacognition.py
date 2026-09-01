"""Unit test suite for SAGI Metacognition & Decision Autopsy Engine."""

import pytest
from sage.experimental.sagi.metacognition import (
    DecisionAutopsy,
    DecisionClassification,
    DecisionRegretRecord,
    MetacognitiveState,
    SAGIDecisionAutopsyEngine,
    SAGIOperationalSelfModel,
)


def test_metacognitive_state_composite_and_calibration():
    """Verify composite confidence calculation and error calibration."""
    m_state = MetacognitiveState(
        knowledge_confidence=0.9,
        inference_confidence=0.8,
        decision_confidence=0.85,
        outcome_confidence=0.75,
        self_calibration_score=0.8,
    )
    composite = m_state.compute_composite_confidence()
    assert 0.8 <= composite <= 0.9

    # High prediction error -> increases risk regulation factor
    m_state.calibrate(prediction_error=0.6)
    assert m_state.risk_regulation_factor > 1.0


def test_decision_regret_record_computation():
    """Verify counterfactual regret computation."""
    regret_rec = DecisionRegretRecord(
        decision_id="dec_001",
        chosen_action="action_A",
        actual_outcome_val=0.4,
        counterfactual_outcomes={
            "action_A": 0.4,
            "action_B": 0.85,
            "action_C": 0.2,
        },
    )
    regret = regret_rec.compute_regret()
    assert regret == pytest.approx(0.45, abs=1e-4)
    assert regret_rec.best_counterfactual_action == "action_B"
    assert regret_rec.max_counterfactual_val == 0.85


def test_autopsy_classification_win_good():
    """Verify WIN_GOOD_DECISION classification."""
    autopsy = SAGIDecisionAutopsyEngine.perform_autopsy(
        decision_id="d1",
        chosen_action="buy",
        expected_outcome_val=0.8,
        actual_outcome_val=0.9,
        decision_quality_score=0.9,
    )
    assert autopsy.classification == DecisionClassification.WIN_GOOD_DECISION
    assert "Reinforce current decision policy" in autopsy.lesson


def test_autopsy_classification_win_bad_false_success():
    """Verify WIN_BAD_DECISION (lucky win / false success) classification."""
    autopsy = SAGIDecisionAutopsyEngine.perform_autopsy(
        decision_id="d2",
        chosen_action="gamble",
        expected_outcome_val=0.2,
        actual_outcome_val=0.85, # Win
        decision_quality_score=0.3, # Bad decision
    )
    assert autopsy.classification == DecisionClassification.WIN_BAD_DECISION
    assert "Do not reinforce flawed policy" in autopsy.lesson


def test_autopsy_classification_loss_good_variance():
    """Verify LOSS_GOOD_DECISION (bad luck / variance) classification."""
    autopsy = SAGIDecisionAutopsyEngine.perform_autopsy(
        decision_id="d3",
        chosen_action="optimal_play",
        expected_outcome_val=0.75,
        actual_outcome_val=0.2, # Unlucky loss
        decision_quality_score=0.85, # High decision quality
    )
    assert autopsy.classification == DecisionClassification.LOSS_GOOD_DECISION
    assert "Environmental variance or bad luck" in autopsy.attribution
    assert "Retain decision policy" in autopsy.lesson


def test_autopsy_classification_loss_bad_genuine_error():
    """Verify LOSS_BAD_DECISION (genuine error) classification."""
    autopsy = SAGIDecisionAutopsyEngine.perform_autopsy(
        decision_id="d4",
        chosen_action="flawed_play",
        expected_outcome_val=0.3,
        actual_outcome_val=0.1,
        decision_quality_score=0.2,
    )
    assert autopsy.classification == DecisionClassification.LOSS_BAD_DECISION
    assert "Genuine error" in autopsy.attribution


def test_operational_self_model_integration():
    """Verify integration of autopsies into the SAGI operational self-model."""
    self_model = SAGIOperationalSelfModel()
    assert self_model.total_autopsies_performed == 0

    autopsy = SAGIDecisionAutopsyEngine.perform_autopsy(
        decision_id="d_test",
        chosen_action="hold",
        expected_outcome_val=0.7,
        actual_outcome_val=0.75,
        decision_quality_score=0.88,
        counterfactual_outcomes={"fold": 0.4, "raise": 0.95},
    )
    self_model.record_autopsy(autopsy, domain="sports_quant")

    assert self_model.total_autopsies_performed == 1
    assert "sports_quant" in self_model.domain_reliability
    summary = self_model.get_governed_summary()
    assert summary["total_autopsies"] == 1
