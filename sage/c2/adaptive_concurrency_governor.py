"""SAGE Adaptive Concurrency Governor.

Analyzes workload parameters (dependency density, resource overlap, verification latency, rework rate)
to derive non-authoritative ConcurrencyProfileCandidates.

Governance Rule:
- Self-Observation, Not Self-Authority: Candidate profiles default to ValidationStatus.HOLD.
  Promotion requires explicit C2 AuthorizationRecord revalidated at execution time.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.c2.experiment_ledger import ValidationStatus


class WorkloadProfile(BaseModel):
    """Input workload metrics evaluated for safe adaptive concurrency limits."""

    workload_id: str
    total_tasks: int
    dependency_density: float = Field(default=0.0, ge=0.0, le=1.0)
    resource_overlap_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_verification_latency_sec: float = Field(default=1.0, ge=0.0)
    historical_rework_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    ci_capacity_limit: int = Field(default=10, ge=1)


class ConcurrencyProfileCandidate(BaseModel):
    """Non-authoritative candidate profile proposing safe worker limits."""

    candidate_id: str
    workload_id: str
    recommended_workers: int
    safe_max_workers: int
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.HOLD
    rationale: str
    provenance_hash: str
    timestamp: float = Field(default_factory=time.time)

    def compute_hash(self) -> str:
        payload = f"{self.candidate_id}:{self.workload_id}:{self.recommended_workers}:{self.safe_max_workers}:{self.confidence_score:.4f}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AdaptiveConcurrencyGovernor:
    """Evaluates workload characteristics and produces non-authoritative concurrency candidates."""

    def evaluate_workload(self, profile: WorkloadProfile) -> ConcurrencyProfileCandidate:
        """Derives recommended worker limits based on workload analysis."""
        cand_id = f"cand_conc_{hashlib.sha256(f'{profile.workload_id}:{time.time()}'.encode()).hexdigest()[:10]}"

        # Base calculations
        base_workers = min(profile.total_tasks, profile.ci_capacity_limit)

        # Penalties based on coupling and verification bottlenecks
        overlap_penalty = int(base_workers * profile.resource_overlap_ratio * 0.5)
        dependency_penalty = int(base_workers * profile.dependency_density * 0.4)
        rework_penalty = int(base_workers * profile.historical_rework_rate * 0.5)

        # Verification latency throttling
        latency_penalty = 0
        if profile.avg_verification_latency_sec > 10.0:
            latency_penalty = 2
        elif profile.avg_verification_latency_sec > 30.0:
            latency_penalty = 4

        recommended = max(1, base_workers - overlap_penalty - dependency_penalty - rework_penalty - latency_penalty)
        safe_max = max(recommended, min(profile.ci_capacity_limit, recommended + 2))

        # Confidence calculation
        confidence = round(
            max(0.1, 1.0 - (profile.resource_overlap_ratio * 0.3 + profile.historical_rework_rate * 0.4 + profile.dependency_density * 0.3)),
            4,
        )

        rationale = (
            f"Evaluated workload {profile.workload_id}: base {base_workers} workers adjusted for "
            f"overlap ({profile.resource_overlap_ratio:.2f}), dependencies ({profile.dependency_density:.2f}), "
            f"and rework ({profile.historical_rework_rate:.2f}). Recommended: {recommended} workers."
        )

        candidate = ConcurrencyProfileCandidate(
            candidate_id=cand_id,
            workload_id=profile.workload_id,
            recommended_workers=recommended,
            safe_max_workers=safe_max,
            confidence_score=confidence,
            validation_status=ValidationStatus.HOLD,
            rationale=rationale,
            provenance_hash="",
        )
        candidate.provenance_hash = candidate.compute_hash()
        return candidate
