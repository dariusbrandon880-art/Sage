"""AIET Mission Runner.

Orchestrates blind scenario execution, failure injection, independent evaluation,
and receipt generation across candidate operating techniques.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet.adapter import AIETControlAdapter
from sage.experimental.aiet.evaluator import AIETIndependentEvaluator
from sage.experimental.aiet.metrics import AIETMetricsCalculator, AIETPerformanceMetrics
from sage.experimental.aiet.perturbation import AIETPerturbationInjector, FailurePerturbation
from sage.experimental.aiet.receipt import AIETValidationReceipt
from sage.experimental.aiet.scenario import AIETBlindScenario


class AIETMissionRunner:
    """Runner for AIET Validation Lab trials."""

    def __init__(self, adapter: Optional[AIETControlAdapter] = None) -> None:
        self.adapter = adapter or AIETControlAdapter()
        self.evaluator = AIETIndependentEvaluator()

    def run_validation_flight(
        self,
        mission_contract: MissionContract,
        scenarios: List[AIETBlindScenario],
        baseline_executor: Callable[[Dict[str, Any]], Dict[str, Any]],
        candidate_executor: Callable[[Dict[str, Any]], Dict[str, Any]],
        perturbations: Optional[List[FailurePerturbation]] = None,
        baseline_technique_id: str = "baseline_v1",
        candidate_technique_id: str = "candidate_v2",
    ) -> AIETValidationReceipt:
        """Run 5 frozen trial phases across scenarios, perturbations, and transfer tasks."""
        perturbation_injector = AIETPerturbationInjector(perturbations or [])
        injected_perturbation_ids = [p.perturbation_id for p in (perturbations or [])]
        scenario_ids = [s.scenario_id for s in scenarios]

        trials_count = 0
        fail_reasons: List[str] = []

        baseline_fitnesses: List[FitnessVector] = []
        candidate_fitnesses: List[FitnessVector] = []
        perturbed_candidate_fitnesses: List[FitnessVector] = []
        transfer_fitnesses: List[FitnessVector] = []

        # Enforce contract path checks if metadata targets exist
        target_paths = mission_contract.metadata.get("target_paths", [])
        contract_violations = mission_contract.check_paths(target_paths)
        if contract_violations:
            fail_reasons.extend([f"CONTRACT_VIOLATION:{v}" for v in contract_violations])

        for idx, scenario in enumerate(scenarios):
            # 1. Baseline trial
            t0 = time.time()
            base_out = baseline_executor(scenario.inputs)
            dt_base = time.time() - t0
            fit_base, _ = self.evaluator.evaluate_run(scenario, base_out, dt_base, cost_unit=1.0)
            baseline_fitnesses.append(fit_base)
            trial_id_base = f"trial_{scenario.scenario_id}_base_{idx}"
            self.adapter.record_trial(
                mission_id=mission_contract.mission_id,
                technique_id=baseline_technique_id,
                trial_id=trial_id_base,
                fitness=fit_base,
                evidence_ref=f"ev_{trial_id_base}",
                adversarial=False,
                regression_free=True,
            )
            trials_count += 1

            # 2. Candidate unperturbed trial
            t0 = time.time()
            cand_out = candidate_executor(scenario.inputs)
            dt_cand = time.time() - t0
            fit_cand, violations_cand = self.evaluator.evaluate_run(scenario, cand_out, dt_cand, cost_unit=0.8)
            candidate_fitnesses.append(fit_cand)
            trial_id_cand = f"trial_{scenario.scenario_id}_cand_{idx}"
            self.adapter.record_trial(
                mission_id=mission_contract.mission_id,
                technique_id=candidate_technique_id,
                trial_id=trial_id_cand,
                fitness=fit_cand,
                evidence_ref=f"ev_{trial_id_cand}",
                adversarial=False,
                regression_free=len(violations_cand) == 0,
            )
            trials_count += 1

            # 3. Candidate perturbed trial
            pert_inputs, pert_logs = perturbation_injector.apply(scenario.inputs)
            t0 = time.time()
            cand_pert_out = candidate_executor(pert_inputs)
            dt_pert = time.time() - t0
            fit_pert, violations_pert = self.evaluator.evaluate_run(scenario, cand_pert_out, dt_pert, cost_unit=0.9)
            perturbed_candidate_fitnesses.append(fit_pert)
            trial_id_pert = f"trial_{scenario.scenario_id}_pert_{idx}"
            self.adapter.record_trial(
                mission_id=mission_contract.mission_id,
                technique_id=candidate_technique_id,
                trial_id=trial_id_pert,
                fitness=fit_pert,
                evidence_ref=f"ev_{trial_id_pert}",
                adversarial=True,
                regression_free=len(violations_pert) == 0,
            )
            trials_count += 1

            # 4. Transfer scenario trial (if present or simulated transfer domain)
            transfer_inputs = dict(scenario.inputs)
            if scenario.transfer_target_domain:
                transfer_inputs["_transfer_domain"] = scenario.transfer_target_domain
            t0 = time.time()
            cand_trans_out = candidate_executor(transfer_inputs)
            dt_trans = time.time() - t0
            fit_trans, _ = self.evaluator.evaluate_run(scenario, cand_trans_out, dt_trans, cost_unit=0.85)
            transfer_fitnesses.append(fit_trans)
            trials_count += 1

        # Mean fitness values for metrics computation
        mean_base = _mean_fit(baseline_fitnesses)
        mean_cand = _mean_fit(candidate_fitnesses)
        mean_pert = _mean_fit(perturbed_candidate_fitnesses)
        mean_trans = _mean_fit(transfer_fitnesses)

        metrics = AIETMetricsCalculator.calculate_metrics(
            baseline_fitness=mean_base,
            candidate_fitness=mean_cand,
            perturbed_candidate_fitness=mean_pert,
            transfer_fitness=mean_trans,
            regression_free=len(fail_reasons) == 0,
        )

        # Evolution loop evaluation via adapter
        evolution_eval = self.adapter.evaluate_evolution(
            mission_id=mission_contract.mission_id,
            baseline_technique_id=baseline_technique_id,
            candidate_technique_id=candidate_technique_id,
        )

        overall_verdict = (
            "PASS"
            if evolution_eval.decision.value == "PROMOTE_CANDIDATE" and metrics.resilience_score >= 0.70 and not fail_reasons
            else "HOLD"
        )

        receipt_id = f"aiet_rcpt_{int(time.time())}"

        return AIETValidationReceipt(
            receipt_id=receipt_id,
            mission_id=mission_contract.mission_id,
            trials_count=trials_count,
            scenarios_evaluated=scenario_ids,
            perturbations_injected=injected_perturbation_ids,
            baseline_technique_id=baseline_technique_id,
            candidate_technique_id=candidate_technique_id,
            adaptation_gain=metrics.adaptation_gain,
            recovery_rate=metrics.recovery_rate,
            transfer_efficiency=metrics.transfer_efficiency,
            resilience_score=metrics.resilience_score,
            evolution_decision=evolution_eval.decision.value,
            overall_verdict=overall_verdict,
            fail_closed_reasons=tuple(fail_reasons),
        )


def _mean_fit(vectors: List[FitnessVector]) -> FitnessVector:
    if not vectors:
        return FitnessVector(
            mission_value=0.5,
            correctness=0.5,
            repeatability=0.5,
            evidence_quality=0.5,
            recovery=0.5,
            generalization=0.5,
            cost=1.0,
        )
    return FitnessVector(
        mission_value=sum(v.mission_value for v in vectors) / len(vectors),
        correctness=sum(v.correctness for v in vectors) / len(vectors),
        repeatability=sum(v.repeatability for v in vectors) / len(vectors),
        evidence_quality=sum(v.evidence_quality for v in vectors) / len(vectors),
        recovery=sum(v.recovery for v in vectors) / len(vectors),
        generalization=sum(v.generalization for v in vectors) / len(vectors),
        cost=sum(v.cost for v in vectors) / len(vectors),
    )
