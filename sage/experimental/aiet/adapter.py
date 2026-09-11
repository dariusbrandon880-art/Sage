"""Control/Baseline Adapter for AIET.

Interfaces with bounded SAGE C2 mechanisms without creating a second authority layer.
"""

from __future__ import annotations

import subprocess
from typing import Any, Optional, Sequence, Tuple

from sage.c2.evolution_loop import EvolutionEvaluation, EvolutionLoop, FitnessVector
from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial
from sage.c2.governed_continuity_outcome_bridge import (
    GovernedContinuityOutcomeBridge,
    GovernedContinuityOutcomeReceipt,
)
from sage.c2.mission_contract import MissionContract, validate_contract_file


def _get_current_head() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return "0000000000000000000000000000000000000000"


class AIETControlAdapter:
    """Bridge AIET trials to existing bounded C2 evaluation infrastructure."""

    def __init__(self, ledger: Optional[ExperimentLedger] = None) -> None:
        self.ledger = ledger or ExperimentLedger()
        self.evolution_loop = EvolutionLoop(minimum_improvement=0.05)
        self.continuity_bridge = GovernedContinuityOutcomeBridge()

    def load_mission_contract(self, payload_or_path: Any) -> MissionContract:
        if isinstance(payload_or_path, str) and payload_or_path.endswith(".json"):
            return validate_contract_file(payload_or_path)
        if isinstance(payload_or_path, dict):
            return MissionContract.from_mapping(payload_or_path)
        raise ValueError("Invalid mission contract payload or path")

    def record_trial(
        self,
        mission_id: str,
        technique_id: str,
        trial_id: str,
        fitness: FitnessVector,
        evidence_ref: str,
        adversarial: bool = False,
        regression_free: bool = True,
        git_head: Optional[str] = None,
    ) -> str:
        """Record a trial without asserting that a human reviewed it."""
        trial = ExperimentTrial(
            mission_id=mission_id,
            technique_id=technique_id,
            trial_id=trial_id,
            fitness=fitness,
            evidence_ref=evidence_ref,
            exact_git_head=git_head or _get_current_head(),
            adversarial=adversarial,
            regression_free=regression_free,
            human_reviewed=False,
        )
        return self.ledger.append(trial)

    def evaluate_evolution(
        self,
        mission_id: str,
        baseline_technique_id: str,
        candidate_technique_id: str,
    ) -> EvolutionEvaluation:
        baseline = self.ledger.build_baseline(mission_id, baseline_technique_id)
        candidate = self.ledger.build_candidate(mission_id, candidate_technique_id)
        return self.evolution_loop.evaluate(mission_id, baseline, [candidate])

    def execute_continuity_bridge(
        self,
        main_goals: Tuple[str, ...],
        session_id: str,
        baseline_observations: Sequence[Any],
        sage_observations: Sequence[Any],
        evaluation_plan: Any,
        benchmark_baseline: Any,
        benchmark_intervention: Any,
        benchmark_observation: Any,
    ) -> GovernedContinuityOutcomeReceipt:
        return self.continuity_bridge.execute_frontier_evaluation(
            main_goals=main_goals,
            session_id=session_id,
            baseline_observations=baseline_observations,
            sage_observations=sage_observations,
            evaluation_plan=evaluation_plan,
            benchmark_baseline=benchmark_baseline,
            benchmark_intervention=benchmark_intervention,
            benchmark_observation=benchmark_observation,
        )
