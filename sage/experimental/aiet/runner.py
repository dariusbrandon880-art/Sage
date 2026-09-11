"""AIET Validation Lab mission runner.

The runner is an evaluation harness, not an autonomy claim. It executes the frozen
five-phase protocol, records evidence, and fails closed when experimental integrity
cannot be established.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional

from sage.c2.evolution_loop import FitnessVector
from sage.c2.mission_contract import MissionContract
from sage.experimental.aiet.adapter import AIETControlAdapter
from sage.experimental.aiet.evaluator import AIETIndependentEvaluator
from sage.experimental.aiet.metrics import AIETMetricsCalculator
from sage.experimental.aiet.perturbation import AIETPerturbationInjector, FailurePerturbation
from sage.experimental.aiet.receipt import AIETValidationReceipt
from sage.experimental.aiet.scenario import AIETBlindScenario


FROZEN_TRIALS = (
    "SELF_CORRECTION",
    "BASELINE_DISCOVERY",
    "STRATEGY_TRANSFER",
    "ACTIVE_DISRUPTION",
    "NOVEL_SYNTHESIS",
)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AIETMissionRunner:
    """Execute the frozen AIET trial sequence against supplied executors."""

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
        execution_mode: str = "external",
    ) -> AIETValidationReceipt:
        perturbation_injector = AIETPerturbationInjector(perturbations or [])
        perturbation_ids = [p.perturbation_id for p in (perturbations or [])]
        scenario_ids = [s.scenario_id for s in scenarios]
        fail_reasons: List[str] = []
        observations: List[str] = []
        decisions: List[str] = []
        actions: List[str] = []
        failures: List[str] = []
        adaptations: List[str] = []
        knowledge_delta: List[str] = []
        outputs: List[Dict[str, Any]] = []
        baseline_fitnesses: List[FitnessVector] = []
        candidate_fitnesses: List[FitnessVector] = []
        perturbed_fitnesses: List[FitnessVector] = []
        transfer_fitnesses: List[FitnessVector] = []

        target_paths = mission_contract.metadata.get("target_paths", [])
        for violation in mission_contract.check_paths(target_paths):
            fail_reasons.append(f"CONTRACT_VIOLATION:{violation}")

        initial_state = {"mission_id": mission_contract.mission_id, "scenarios": scenario_ids}
        initial_state_hash = _stable_hash(initial_state)
        scenario_hash = _stable_hash([s.dict() for s in scenarios])
        human_interventions = 0
        unscripted_discovery = True
        constraint_integrity = True
        verification_integrity = True
        adaptation_latency_steps = 0

        for scenario_index, scenario in enumerate(scenarios):
            phase_outputs: Dict[str, Dict[str, Any]] = {}
            for phase in FROZEN_TRIALS:
                inputs = dict(scenario.inputs)
                inputs["_trial_phase"] = phase
                inputs["_scenario_index"] = scenario_index

                if phase == "SELF_CORRECTION":
                    inputs["_strategy_invalidated"] = True
                    executor = candidate_executor
                elif phase == "BASELINE_DISCOVERY":
                    executor = baseline_executor
                elif phase == "STRATEGY_TRANSFER":
                    inputs["_transfer_domain"] = scenario.transfer_target_domain
                    inputs["_retained_knowledge"] = list(knowledge_delta)
                    executor = candidate_executor
                elif phase == "ACTIVE_DISRUPTION":
                    inputs, perturb_logs = perturbation_injector.apply(inputs)
                    actions.extend(perturb_logs)
                    executor = candidate_executor
                else:
                    inputs["_novel_domain"] = f"NOVEL::{scenario.domain}"
                    inputs["_retained_knowledge"] = list(knowledge_delta)
                    executor = candidate_executor

                started = time.time()
                output = executor(inputs)
                elapsed = time.time() - started
                if not isinstance(output, dict):
                    failures.append(f"NON_MAPPING_OUTPUT:{scenario.scenario_id}:{phase}")
                    output = {}

                outputs.append(output)
                phase_outputs[phase] = output
                passed, violations = self.evaluator.evaluate_run(scenario, output, elapsed, cost_unit=1.0)
                if violations:
                    constraint_integrity = False
                    failures.extend(f"{scenario.scenario_id}:{phase}:{v}" for v in violations)

                if int(output.get("human_intervention_count", 0)) > 0:
                    human_interventions += int(output["human_intervention_count"])
                if output.get("verification_integrity") is False:
                    verification_integrity = False
                if output.get("constraint_integrity") is False:
                    constraint_integrity = False
                if output.get("unscripted_discovery") is False:
                    unscripted_discovery = False
                adaptation_latency_steps = max(adaptation_latency_steps, int(output.get("adaptation_latency_steps", 0)))

                observations.append(str(output.get("observation", f"{phase}:{scenario.scenario_id}")))
                decisions.append(str(output.get("decision", phase)))
                actions.append(str(output.get("action", phase)))
                if output.get("adaptation"):
                    adaptations.append(str(output["adaptation"]))
                if output.get("knowledge_delta"):
                    knowledge_delta.append(str(output["knowledge_delta"]))

                trial_id = f"trial_{scenario.scenario_id}_{phase.lower()}_{scenario_index}"
                self.adapter.record_trial(
                    mission_id=mission_contract.mission_id,
                    technique_id=baseline_technique_id if phase == "BASELINE_DISCOVERY" else candidate_technique_id,
                    trial_id=trial_id,
                    fitness=passed,
                    evidence_ref=f"ev_{trial_id}",
                    adversarial=phase == "ACTIVE_DISRUPTION",
                    regression_free=not violations,
                )

                if phase == "BASELINE_DISCOVERY":
                    baseline_fitnesses.append(passed)
                elif phase == "STRATEGY_TRANSFER":
                    transfer_fitnesses.append(passed)
                    candidate_fitnesses.append(passed)
                elif phase == "ACTIVE_DISRUPTION":
                    perturbed_fitnesses.append(passed)
                else:
                    candidate_fitnesses.append(passed)

        if not baseline_fitnesses or not candidate_fitnesses or not perturbed_fitnesses or not transfer_fitnesses:
            fail_reasons.append("INCOMPLETE_FROZEN_TRIAL_SEQUENCE")

        def mean_fit(values: List[FitnessVector]) -> FitnessVector:
            if not values:
                return FitnessVector(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
            return FitnessVector(
                mission_value=sum(v.mission_value for v in values) / len(values),
                correctness=sum(v.correctness for v in values) / len(values),
                repeatability=sum(v.repeatability for v in values) / len(values),
                evidence_quality=sum(v.evidence_quality for v in values) / len(values),
                recovery=sum(v.recovery for v in values) / len(values),
                generalization=sum(v.generalization for v in values) / len(values),
                cost=sum(v.cost for v in values) / len(values),
            )

        metrics = AIETMetricsCalculator.calculate_metrics(
            baseline_fitness=mean_fit(baseline_fitnesses),
            candidate_fitness=mean_fit(candidate_fitnesses),
            perturbed_candidate_fitness=mean_fit(perturbed_fitnesses),
            transfer_fitness=mean_fit(transfer_fitnesses),
            regression_free=not failures,
        )
        evolution_eval = self.adapter.evaluate_evolution(
            mission_id=mission_contract.mission_id,
            baseline_technique_id=baseline_technique_id,
            candidate_technique_id=candidate_technique_id,
        )

        # The existing EvolutionLoop decision is an evaluation signal only; it is not
        # promotion authority. Fixture/synthetic executors can never produce an
        # autonomy verdict, even when their metrics are favorable.
        if execution_mode != "external":
            verdict = "AUTOMATION"
            fail_reasons.append(f"NON_EXTERNAL_EXECUTION:{execution_mode}")
        elif human_interventions != 0:
            verdict = "INVALID_EXPERIMENT"
            fail_reasons.append("HUMAN_INTERVENTION_DETECTED")
        elif not constraint_integrity or not verification_integrity:
            verdict = "INVALID_EXPERIMENT"
        elif not unscripted_discovery:
            verdict = "AUTOMATION"
        elif metrics.resilience_score >= 0.70 and not fail_reasons:
            verdict = "DEMONSTRATED_AUTONOMOUS_ADAPTATION"
        else:
            verdict = "PARTIAL_AUTONOMY"

        final_state_hash = _stable_hash(outputs)
        transfer_result = {
            "target_domains": [s.transfer_target_domain for s in scenarios],
            "transfer_efficiency": metrics.transfer_efficiency,
            "retained_knowledge_count": len(knowledge_delta),
        }

        return AIETValidationReceipt(
            receipt_id=f"aiet_rcpt_{int(time.time())}",
            mission_id=mission_contract.mission_id,
            trials_count=len(scenarios) * len(FROZEN_TRIALS),
            scenarios_evaluated=scenario_ids,
            perturbations_injected=perturbation_ids,
            baseline_technique_id=baseline_technique_id,
            candidate_technique_id=candidate_technique_id,
            adaptation_gain=metrics.adaptation_gain,
            recovery_rate=metrics.recovery_rate,
            transfer_efficiency=metrics.transfer_efficiency,
            resilience_score=metrics.resilience_score,
            evolution_decision=evolution_eval.decision.value,
            overall_verdict=verdict,
            isolation_status="UNVERIFIED" if execution_mode != "external" else "REQUIRES_HARNESS_PROOF",
            initial_state_hash=initial_state_hash,
            scenario_hash=scenario_hash,
            observations=observations,
            decisions=decisions,
            actions=actions,
            failures=failures,
            adaptations=adaptations,
            constraint_integrity=constraint_integrity,
            verification_integrity=verification_integrity,
            human_intervention_count=human_interventions,
            unscripted_discovery=unscripted_discovery,
            adaptation_latency_steps=adaptation_latency_steps,
            knowledge_delta_retained=knowledge_delta,
            transfer_result=transfer_result,
            final_state_hash=final_state_hash,
            verdict=verdict,
            execution_mode=execution_mode,
            fail_closed_reasons=tuple(fail_reasons),
        )
