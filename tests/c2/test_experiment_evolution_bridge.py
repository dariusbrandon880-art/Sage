from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial
from sage.c2.evolution_loop import EvolutionLoop, EvolutionDecision, FitnessVector


def make_trial(technique: str, trial_id: str, value: float, **flags):
    return ExperimentTrial(
        mission_id="mission",
        technique_id=technique,
        trial_id=trial_id,
        fitness=FitnessVector(
            mission_value=value, correctness=value, repeatability=value,
            evidence_quality=value, recovery=value, generalization=value, cost=1.0,
        ),
        evidence_ref=f"evidence:{trial_id}",
        exact_git_head="a" * 40,
        regression_free=True,
        **flags,
    )


def test_real_ledger_to_evolution_path():
    ledger = ExperimentLedger()
    ledger.append(make_trial("baseline", "b1", 0.70, human_reviewed=True))
    ledger.append(make_trial("candidate", "c1", 0.90, human_reviewed=True))
    ledger.append(make_trial("candidate", "c2", 0.90, adversarial=True, human_reviewed=True))

    result = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "mission",
        ledger.build_baseline("mission", "baseline"),
        [ledger.build_candidate("mission", "candidate")],
    )

    assert result.decision is EvolutionDecision.PROMOTE_CANDIDATE
    assert result.winner == "candidate"
    assert result.promotion_authorized is False


def test_missing_counterexample_keeps_candidate_on_hold():
    ledger = ExperimentLedger()
    ledger.append(make_trial("baseline", "b1", 0.70, human_reviewed=True))
    ledger.append(make_trial("candidate", "c1", 0.90, human_reviewed=True))
    ledger.append(make_trial("candidate", "c2", 0.90, human_reviewed=True))

    result = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "mission",
        ledger.build_baseline("mission", "baseline"),
        [ledger.build_candidate("mission", "candidate")],
    )

    assert result.decision is EvolutionDecision.HOLD
