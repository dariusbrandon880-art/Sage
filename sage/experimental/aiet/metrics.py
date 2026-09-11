"""Adaptation & Transfer Metrics Calculator for AIET.

Calculates normalized operational metrics:
- Adaptation Gain: Relative fitness improvement under non-perturbed and perturbed scenarios.
- Recovery Rate: Ability to maintain/recover performance under failure injections.
- Transfer Efficiency: Performance retention across unseen target domains.
- Resilience Score: Weighted composite of recovery rate, correctness, and evidence completeness.
"""

from __future__ import annotations

from typing import List, Sequence
from pydantic import BaseModel, Field

from sage.c2.evolution_loop import FitnessVector


class AIETPerformanceMetrics(BaseModel):
    """Normalized metrics output for an AIET trial or batch."""

    adaptation_gain: float = Field(ge=0.0)
    recovery_rate: float = Field(ge=0.0, le=1.0)
    transfer_efficiency: float = Field(ge=0.0, le=1.0)
    resilience_score: float = Field(ge=0.0, le=1.0)


class AIETMetricsCalculator:
    """Computes adaptation, recovery, transfer, and resilience metrics."""

    @staticmethod
    def calculate_metrics(
        baseline_fitness: FitnessVector,
        candidate_fitness: FitnessVector,
        perturbed_candidate_fitness: FitnessVector,
        transfer_fitness: FitnessVector,
        regression_free: bool = True,
    ) -> AIETPerformanceMetrics:
        b_score = baseline_fitness.score()
        c_score = candidate_fitness.score()
        p_score = perturbed_candidate_fitness.score()
        t_score = transfer_fitness.score()

        # Adaptation gain: candidate vs baseline score improvement ratio
        adaptation_gain = (c_score / b_score) - 1.0 if b_score > 0 else 0.0
        if adaptation_gain < 0:
            adaptation_gain = 0.0

        # Recovery rate: performance under perturbation relative to unperturbed candidate score
        recovery_rate = min(1.0, max(0.0, p_score / c_score)) if c_score > 0 else 0.0

        # Transfer efficiency: performance in transfer domain relative to primary candidate score
        transfer_efficiency = min(1.0, max(0.0, t_score / c_score)) if c_score > 0 else 0.0

        # Resilience score: composite of recovery rate, candidate correctness, and regression status
        reg_penalty = 1.0 if regression_free else 0.5
        resilience_score = min(
            1.0,
            max(
                0.0,
                (0.5 * recovery_rate + 0.3 * candidate_fitness.correctness + 0.2 * candidate_fitness.recovery)
                * reg_penalty,
            ),
        )

        return AIETPerformanceMetrics(
            adaptation_gain=round(adaptation_gain, 4),
            recovery_rate=round(recovery_rate, 4),
            transfer_efficiency=round(transfer_efficiency, 4),
            resilience_score=round(resilience_score, 4),
        )
