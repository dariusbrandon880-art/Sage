"""C2 Reconvergence Evidence Synthesizer & Promotion Gate.

Aggregates 5-flight execution receipts across 5x4 lifecycle milestone gates,
verifies 100% first-pass verification pass rate, and outputs canonical SHA-256 evidence package.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FlightExecutionSummary(BaseModel):
    """Execution summary for a single flight in a wave."""
    flight_id: str
    target: str
    classification: str
    execution_result: str
    exact_head: str
    tests_passed: int
    evidence_ref: str
    pr_or_change: str
    blocker: Optional[str] = None


class ReconvergenceEvidencePackage(BaseModel):
    """Immutable evidence package generated during wave reconvergence."""
    wave_id: str
    flight_summaries: List[FlightExecutionSummary]
    total_flights: int
    successful_flights: int
    blocked_flights: int
    first_pass_verification_rate: float
    reconvergence_verdict: str
    timestamp: float = Field(default_factory=time.time)
    package_hash: str = ""

    def compute_hash(self) -> str:
        flights_blob = ";".join([f"{f.flight_id}:{f.execution_result}:{f.exact_head}" for f in self.flight_summaries])
        payload = f"{self.wave_id}:{self.total_flights}:{self.successful_flights}:{self.first_pass_verification_rate}:{self.reconvergence_verdict}:{flights_blob}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class C2ReconvergenceSynthesizer:
    """Synthesizer aggregating wave execution evidence and evaluating promotion readiness."""

    def __init__(self, wave_id: str):
        self.wave_id = wave_id

    def synthesize_reconvergence(
        self,
        flight_summaries: List[FlightExecutionSummary]
    ) -> ReconvergenceEvidencePackage:
        """Synthesizes evidence package and determines reconvergence verdict."""
        total = len(flight_summaries)
        successful = sum(1 for f in flight_summaries if f.execution_result.upper() in ("PASS", "SUCCESS", "EXECUTED"))
        blocked = sum(1 for f in flight_summaries if f.blocker is not None or f.execution_result.upper() == "BLOCKED")

        rate = (successful / total * 100.0) if total > 0 else 0.0

        verdict = "PASS" if (successful == total and blocked == 0 and total == 5) else "FAIL_CLOSED"

        pkg = ReconvergenceEvidencePackage(
            wave_id=self.wave_id,
            flight_summaries=flight_summaries,
            total_flights=total,
            successful_flights=successful,
            blocked_flights=blocked,
            first_pass_verification_rate=rate,
            reconvergence_verdict=verdict,
        )
        pkg.package_hash = pkg.compute_hash()
        return pkg
