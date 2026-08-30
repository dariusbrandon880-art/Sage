"""Append-only experiment evidence ledger for bounded SAGE evolution trials.

The ledger records measured trials and derives an EvolutionBaseline plus
EvolutionCandidate from the same persisted observations. It never authorizes
promotion and fails closed when a technique lacks sufficient evidence.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Iterable

from pydantic import BaseModel, Field

from sage.c2.evolution_loop import EvolutionBaseline, EvolutionCandidate, FitnessVector


class ExperimentTrial(BaseModel):
    """One reproducible observation belonging to a mission/technique."""

    mission_id: str
    technique_id: str
    trial_id: str
    fitness: FitnessVector
    evidence_ref: str
    exact_git_head: str
    adversarial: bool = False
    regression_free: bool = False
    human_reviewed: bool = False
    timestamp: float = Field(default_factory=time.time)

    def digest(self) -> str:
        payload = self.model_dump_json(exclude={"timestamp"})
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ExperimentLedger:
    """In-memory append-only ledger; persistence is supplied by the caller."""

    def __init__(self) -> None:
        self._trials: list[ExperimentTrial] = []

    def append(self, trial: ExperimentTrial) -> str:
        if any(t.trial_id == trial.trial_id for t in self._trials):
            raise ValueError(f"duplicate trial_id: {trial.trial_id}")
        if not trial.exact_git_head or len(trial.exact_git_head) != 40:
            raise ValueError("exact_git_head must be a 40-character commit SHA")
        self._trials.append(trial)
        return trial.digest()

    def trials(self, mission_id: str, technique_id: str | None = None) -> list[ExperimentTrial]:
        return [
            t for t in self._trials
            if t.mission_id == mission_id and (technique_id is None or t.technique_id == technique_id)
        ]

    def build_baseline(self, mission_id: str, technique_id: str) -> EvolutionBaseline:
        trials = self.trials(mission_id, technique_id)
        if not trials:
            raise ValueError("cannot build baseline without ledger trials")
        return EvolutionBaseline(
            technique_id=technique_id,
            trials=len(trials),
            fitness=_mean_fitness(t.fitness for t in trials),
        )

    def build_candidate(self, mission_id: str, technique_id: str) -> EvolutionCandidate:
        trials = self.trials(mission_id, technique_id)
        if not trials:
            raise ValueError("cannot build candidate without ledger trials")
        return EvolutionCandidate(
            technique_id=technique_id,
            trials=len(trials),
            fitness=_mean_fitness(t.fitness for t in trials),
            replicated=len(trials) >= 2,
            adversarially_challenged=any(t.adversarial for t in trials),
            regression_free=all(t.regression_free for t in trials),
            evidence_complete=all(bool(t.evidence_ref) and bool(t.exact_git_head) for t in trials),
            human_reviewed=all(t.human_reviewed for t in trials),
        )

    def export_json(self) -> str:
        return json.dumps([t.model_dump() for t in self._trials], sort_keys=True, indent=2)


def _mean_fitness(vectors: Iterable[FitnessVector]) -> FitnessVector:
    values = list(vectors)
    if not values:
        raise ValueError("at least one fitness vector is required")
    fields = FitnessVector.model_fields
    return FitnessVector(**{
        name: sum(getattr(v, name) for v in values) / len(values)
        for name in fields
    })
