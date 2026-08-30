from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial
from sage.c2.evolution_loop import EvolutionLoop, FitnessVector, EvolutionDecision


SHA = "a" * 40


def fitness(value: float) -> FitnessVector:
    return FitnessVector(
        mission_value=value,
        correctness=value,
        repeatability=value,
        evidence_quality=value,
        recovery=value,
        generalization=value,
        cost=1.0,
    )


def trial(technique: str, trial_id: str, value: float, *, adversarial=False, reviewed=False):
    return ExperimentTrial(
        mission_id="mission-1",
        technique_id=technique,
        trial_id=trial_id,
        fitness=fitness(value),
        evidence_ref=f"evidence/{trial_id}",
        exact_git_head=SHA,
        adversarial=adversarial,
        regression_free=True,
        human_reviewed=reviewed,
    )


def test_ledger_builds_measured_baseline_and_candidate():
    ledger = ExperimentLedger()
    ledger.append(trial("baseline", "b1", 0.70))
    ledger.append(trial("candidate", "c1", 0.90, reviewed=True))
    ledger.append(trial("candidate", "c2", 0.90, adversarial=True, reviewed=True))

    baseline = ledger.build_baseline("mission-1", "baseline")
    candidate = ledger.build_candidate("mission-1", "candidate")
    evaluation = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "mission-1", baseline, [candidate]
    )

    assert candidate.trials == 2
    assert candidate.replicated
    assert candidate.adversarially_challenged
    assert candidate.evidence_complete
    assert candidate.human_reviewed
    assert evaluation.decision is EvolutionDecision.PROMOTE_CANDIDATE
    assert not evaluation.promotion_authorized


def test_ledger_fails_closed_without_replication_or_review():
    ledger = ExperimentLedger()
    ledger.append(trial("baseline", "b1", 0.70))
    ledger.append(trial("candidate", "c1", 0.90))
    candidate = ledger.build_candidate("mission-1", "candidate")
    evaluation = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "mission-1", ledger.build_baseline("mission-1", "baseline"), [candidate]
    )
    assert evaluation.decision is EvolutionDecision.HOLD
    assert not evaluation.promotion_authorized


def test_duplicate_trial_ids_are_rejected():
    ledger = ExperimentLedger()
    ledger.append(trial("baseline", "same", 0.70))
    try:
        ledger.append(trial("candidate", "same", 0.90))
    except ValueError as exc:
        assert "duplicate trial_id" in str(exc)
    else:
        raise AssertionError("duplicate trial_id was accepted")
