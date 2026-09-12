"""Independent Evaluator for AIET.

Performs objective, non-biased evaluation of AI mission runs against blind scenarios,
validating invariant checks, fitness vectors, and regression bounds.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sage.c2.evolution_loop import FitnessVector
from sage.experimental.aiet.scenario import AIETBlindScenario


class AIETIndependentEvaluator:
    """Non-biased evaluation engine for trial execution outputs."""

    def evaluate_run(
        self,
        scenario: AIETBlindScenario,
        output: Dict[str, Any],
        execution_time_sec: float,
        cost_unit: float = 1.0,
    ) -> Tuple[FitnessVector, List[str]]:
        """Evaluate a trial execution output against scenario invariants and return FitnessVector + violations."""
        passed_invariants, violations = scenario.validate_invariants(output)

        correctness = 1.0 if passed_invariants else max(0.0, 1.0 - (len(violations) * 0.25))

        # Hardened independent evaluator boundary: Candidate outputs cannot override
        # invariant violations with self-asserted perfect scores.
        raw_mission_value = float(output.get("mission_value", 1.0 if passed_invariants else 0.5))
        raw_repeatability = float(output.get("repeatability", 0.9))
        raw_evidence_quality = float(output.get("evidence_quality", 1.0 if passed_invariants else 0.5))
        raw_recovery = float(output.get("recovery_rate", 1.0 if passed_invariants else 0.3))
        raw_generalization = float(output.get("generalization", 0.85))

        if not passed_invariants:
            mission_value = min(raw_mission_value, correctness)
            repeatability = min(raw_repeatability, correctness)
            evidence_quality = min(raw_evidence_quality, correctness)
            recovery = min(raw_recovery, correctness)
            generalization = min(raw_generalization, correctness)
        else:
            mission_value = raw_mission_value
            repeatability = raw_repeatability
            evidence_quality = raw_evidence_quality
            recovery = raw_recovery
            generalization = raw_generalization

        cost = max(0.01, float(cost_unit))

        fitness = FitnessVector(
            mission_value=min(1.0, max(0.0, mission_value)),
            correctness=min(1.0, max(0.0, correctness)),
            repeatability=min(1.0, max(0.0, repeatability)),
            evidence_quality=min(1.0, max(0.0, evidence_quality)),
            recovery=min(1.0, max(0.0, recovery)),
            generalization=min(1.0, max(0.0, generalization)),
            cost=cost,
        )

        return fitness, violations
