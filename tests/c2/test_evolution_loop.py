from sage.c2.evolution_loop import (
    EvolutionBaseline,
    EvolutionCandidate,
    EvolutionDecision,
    EvolutionLoop,
    FitnessVector,
)


def vector(*, correctness=0.9, evidence_quality=0.9, cost=0.5):
    return FitnessVector(
        mission_value=0.9,
        correctness=correctness,
        repeatability=0.9,
        evidence_quality=evidence_quality,
        recovery=0.9,
        generalization=0.9,
        cost=cost,
    )


def baseline():
    return EvolutionBaseline(technique_id="baseline", trials=20, fitness=vector(cost=0.7))


def candidate(**kwargs):
    values = dict(
        technique_id="candidate-a",
        trials=20,
        fitness=vector(cost=0.5),
        replicated=True,
        adversarially_challenged=True,
        regression_free=True,
        evidence_complete=True,
        human_reviewed=True,
    )
    values.update(kwargs)
    return EvolutionCandidate(**values)


def test_measured_winner_can_be_recommended_but_never_authorized():
    evaluation = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "MISSION-1", baseline(), [candidate()]
    )

    assert evaluation.winner == "candidate-a"
    assert evaluation.decision is EvolutionDecision.PROMOTE_CANDIDATE
    assert evaluation.promotion_authorized is False


def test_missing_validation_gate_holds_candidate():
    evaluation = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "MISSION-2",
        baseline(),
        [candidate(adversarially_challenged=False)],
    )

    assert evaluation.decision is EvolutionDecision.HOLD
    assert "gates" in evaluation.reason


def test_insufficient_improvement_holds_candidate():
    base = EvolutionBaseline(technique_id="baseline", trials=20, fitness=vector(cost=0.5))
    evaluation = EvolutionLoop(minimum_improvement=0.20).evaluate(
        "MISSION-3", base, [candidate(cost=0.5)]
    )

    assert evaluation.decision is EvolutionDecision.HOLD
    assert "below threshold" in evaluation.reason


def test_no_candidates_holds():
    evaluation = EvolutionLoop().evaluate("MISSION-4", baseline(), [])

    assert evaluation.winner is None
    assert evaluation.decision is EvolutionDecision.HOLD
    assert evaluation.ranked_scores == {}
