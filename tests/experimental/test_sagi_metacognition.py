import pytest

from sage.experimental.sagi.metacognition import MetacognitiveEngine, MetacognitiveState


def make_state(**overrides):
    values = dict(
        knowledge_confidence=0.9,
        inference_confidence=0.8,
        decision_confidence=0.7,
        outcome_confidence=0.0,
        risk_tolerance=0.5,
        risk_score=0.3,
    )
    values.update(overrides)
    return MetacognitiveState(**values)


def test_composite_confidence_uses_weakest_decision_dimension():
    state = make_state(knowledge_confidence=0.6, inference_confidence=0.8, decision_confidence=0.7)
    assert state.composite_confidence == 0.6
    assert state.uncertainty == pytest.approx(0.4)


def test_risk_regulation_exposes_excess_without_acting():
    state = make_state(risk_tolerance=0.4, risk_score=0.75)
    assert state.risk_regulation_score == pytest.approx(0.35)
    assessment = MetacognitiveEngine().assess(state)
    assert assessment.review_required
    assert not assessment.action_allowed
    assert "risk exceeds tolerance" in assessment.reasons


def test_clean_state_is_action_allowed():
    assessment = MetacognitiveEngine().assess(make_state())
    assert assessment.action_allowed
    assert not assessment.review_required
    assert assessment.reasons == ()


def test_unknowns_force_review():
    assessment = MetacognitiveEngine().assess(make_state(unknowns=("lineup-change",)))
    assert assessment.review_required
    assert not assessment.action_allowed


def test_degraded_state_forces_review():
    assessment = MetacognitiveEngine().assess(make_state(degraded=True))
    assert assessment.review_required
    assert not assessment.action_allowed


def test_outcome_update_returns_new_immutable_state():
    state = make_state()
    updated = state.with_outcome(0.2)
    assert state.outcome_confidence == 0.0
    assert updated.outcome_confidence == 0.2
    assert updated.calibration_error == pytest.approx(0.5)


def test_invalid_confidence_and_duplicate_context_fail_closed():
    with pytest.raises(ValueError):
        make_state(decision_confidence=1.1)
    with pytest.raises(ValueError):
        make_state(unknowns=("x", "x"))
    with pytest.raises(ValueError):
        make_state(assumptions=("x", "x"))
