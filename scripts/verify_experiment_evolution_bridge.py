"""Run a deterministic smoke check for the ExperimentLedger -> EvolutionLoop bridge."""
from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial
from sage.c2.evolution_loop import EvolutionLoop, FitnessVector, EvolutionDecision

SHA = "0" * 40


def fv(value: float) -> FitnessVector:
    return FitnessVector(
        mission_value=value, correctness=value, repeatability=value,
        evidence_quality=value, recovery=value, generalization=value, cost=1.0,
    )


def main() -> None:
    ledger = ExperimentLedger()
    ledger.append(ExperimentTrial(mission_id="bridge-smoke", technique_id="baseline", trial_id="b1", fitness=fv(0.70), evidence_ref="e:b1", exact_git_head=SHA, regression_free=True, human_reviewed=True))
    ledger.append(ExperimentTrial(mission_id="bridge-smoke", technique_id="candidate", trial_id="c1", fitness=fv(0.90), evidence_ref="e:c1", exact_git_head=SHA, regression_free=True, human_reviewed=True))
    ledger.append(ExperimentTrial(mission_id="bridge-smoke", technique_id="candidate", trial_id="c2", fitness=fv(0.90), evidence_ref="e:c2", exact_git_head=SHA, adversarial=True, regression_free=True, human_reviewed=True))
    evaluation = EvolutionLoop(minimum_improvement=0.01).evaluate(
        "bridge-smoke",
        ledger.build_baseline("bridge-smoke", "baseline"),
        [ledger.build_candidate("bridge-smoke", "candidate")],
    )
    assert evaluation.decision is EvolutionDecision.PROMOTE_CANDIDATE
    assert not evaluation.promotion_authorized
    print("EXPERIMENT_EVOLUTION_BRIDGE_SMOKE: PASS")


if __name__ == "__main__":
    main()
