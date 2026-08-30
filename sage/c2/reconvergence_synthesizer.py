"""C2 Reconvergence Evidence Synthesizer & Promotion Gate.

Aggregates 5-flight execution receipts across the canonical 5x4 20-cell lifecycle matrix:
- 5 Parallel Paths x 4 Lifecycle Milestone Gates (INTAKE_RECON, BOUNDED_BUILD, VERIFY_PROOF, WAREHOUSE_PROMOTE).
- Validates exact-HEAD commit SHA provenance.
- Verifies 100% first-pass verification pass rate and outputs canonical SHA-256 evidence package.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LifecycleStage(str, Enum):
    """The four canonical milestone gates in the 5x4 frame."""
    INTAKE_RECON = "STAGE_1_INTAKE_RECON"
    BOUNDED_BUILD = "STAGE_2_BOUNDED_BUILD"
    VERIFY_PROOF = "STAGE_3_VERIFY_PROOF"
    WAREHOUSE_PROMOTE = "STAGE_4_WAREHOUSE_PROMOTE"


class LifecycleMilestoneRecord(BaseModel):
    """Record of a single flight passing a lifecycle milestone gate."""
    stage: LifecycleStage
    passed: bool
    evidence_ref: str
    timestamp: float = Field(default_factory=time.time)


class FlightExecutionSummary(BaseModel):
    """Execution summary for a single flight in a wave traversing all lifecycle gates."""
    flight_id: str
    target: str
    classification: str
    execution_result: str
    exact_head: str
    tests_passed: int
    evidence_ref: str
    pr_or_change: str
    lifecycle_milestones: List[LifecycleMilestoneRecord] = Field(default_factory=list)
    blocker: Optional[str] = None

    def completed_all_stages(self) -> bool:
        """Returns True if all 4 canonical lifecycle stages were passed."""
        passed_stages = {m.stage for m in self.lifecycle_milestones if m.passed}
        return len(passed_stages) == 4


class ReconvergenceEvidencePackage(BaseModel):
    """Immutable evidence package generated during wave reconvergence."""
    wave_id: str
    flight_summaries: List[FlightExecutionSummary]
    total_flights: int
    successful_flights: int
    blocked_flights: int
    advancement_matrix_20_cells: Dict[str, bool] = Field(default_factory=dict)
    first_pass_verification_rate: float
    reconvergence_verdict: str
    timestamp: float = Field(default_factory=time.time)
    package_hash: str = ""

    def compute_hash(self) -> str:
        flights_blob = ";".join([f"{f.flight_id}:{f.execution_result}:{f.exact_head}" for f in self.flight_summaries])
        matrix_blob = ";".join([f"{k}={v}" for k, v in sorted(self.advancement_matrix_20_cells.items())])
        payload = f"{self.wave_id}:{self.total_flights}:{self.successful_flights}:{self.first_pass_verification_rate}:{self.reconvergence_verdict}:{flights_blob}:{matrix_blob}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class C2ReconvergenceSynthesizer:
    """Synthesizer aggregating wave execution evidence and evaluating 5x4 promotion readiness."""

    def __init__(self, wave_id: str):
        self.wave_id = wave_id

    def synthesize_reconvergence(
        self,
        flight_summaries: List[FlightExecutionSummary]
    ) -> ReconvergenceEvidencePackage:
        """Synthesizes evidence package, evaluates 20-cell matrix traversal and exact SHA provenance."""
        total = len(flight_summaries)
        successful = 0
        blocked = 0

        advancement_matrix: Dict[str, bool] = {}
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")

        for idx, flight in enumerate(flight_summaries, start=1):
            path_id = f"P{idx}"
            is_valid_sha = bool(sha_pattern.match(flight.exact_head))
            is_active_or_ready = flight.classification.upper() in ("ACTIVE", "READY")
            all_milestones_passed = flight.completed_all_stages()

            # Map the 4 lifecycle stages into the 20-cell advancement matrix
            stages = [
                LifecycleStage.INTAKE_RECON,
                LifecycleStage.BOUNDED_BUILD,
                LifecycleStage.VERIFY_PROOF,
                LifecycleStage.WAREHOUSE_PROMOTE,
            ]
            for s_idx, stage in enumerate(stages, start=1):
                cell_id = f"{path_id}-S{s_idx}"
                milestone_passed = any(m.stage == stage and m.passed for m in flight.lifecycle_milestones)
                advancement_matrix[cell_id] = milestone_passed

            is_success = (
                flight.execution_result.upper() in ("PASS", "SUCCESS", "EXECUTED")
                and is_valid_sha
                and is_active_or_ready
                and all_milestones_passed
                and flight.blocker is None
            )

            if is_success:
                successful += 1
            else:
                blocked += 1

        rate = (successful / total * 100.0) if total > 0 else 0.0
        all_20_cells_passed = len(advancement_matrix) == 20 and all(advancement_matrix.values())

        verdict = "PASS" if (successful == total and blocked == 0 and total == 5 and all_20_cells_passed) else "FAIL_CLOSED"

        pkg = ReconvergenceEvidencePackage(
            wave_id=self.wave_id,
            flight_summaries=flight_summaries,
            total_flights=total,
            successful_flights=successful,
            blocked_flights=blocked,
            advancement_matrix_20_cells=advancement_matrix,
            first_pass_verification_rate=rate,
            reconvergence_verdict=verdict,
        )
        pkg.package_hash = pkg.compute_hash()
        return pkg

    def get_matrix_stage_breakdown(
        self,
        package: ReconvergenceEvidencePackage,
    ) -> Dict[str, Dict[str, Any]]:
        """Extract stage-by-stage pass rate breakdown across the 5x4 matrix."""
        stages = [
            LifecycleStage.INTAKE_RECON,
            LifecycleStage.BOUNDED_BUILD,
            LifecycleStage.VERIFY_PROOF,
            LifecycleStage.WAREHOUSE_PROMOTE,
        ]
        breakdown = {}
        total_flights = max(1, package.total_flights)

        for s_idx, stage in enumerate(stages, start=1):
            cell_keys = [f"P{p_idx}-S{s_idx}" for p_idx in range(1, total_flights + 1)]
            passed_cells = sum(1 for k in cell_keys if package.advancement_matrix_20_cells.get(k, False))
            breakdown[stage.value] = {
                "stage": stage.value,
                "passed_count": passed_cells,
                "total_count": total_flights,
                "pass_rate": (passed_cells / total_flights) * 100.0,
            }

        return breakdown
