"""SAGE Operational Reliability Metrics & Analysis Engine.

Provides a read-only projection engine analyzing repeated operational cycles, failure categories,
evidence completeness, and transition durations across execution observation receipts without
modifying source records or granting execution approvals.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.execution_observability import (
    ExecutionObservationReceipt,
    ExecutionObservationTracker,
)


class OperationalReliabilityRecord(BaseModel):
    """Durable record projecting operational reliability metrics across repeated SAGE cycles."""

    execution_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    blocked_count: int = 0
    review_required_count: int = 0
    average_transition_duration: float = 0.0
    evidence_completeness_ratio: float = 0.0
    duplicate_attempts_count: int = 0
    integrity_failures_count: int = 0
    reliability_score: float = 1.0  # 0.0 to 1.0 score
    failure_category_breakdown: Dict[str, int] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sha256_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.sha256_hash:
            self.sha256_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Computes deterministic SHA-256 hash over canonical JSON metrics representation."""
        payload = {
            "execution_count": self.execution_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "blocked_count": self.blocked_count,
            "review_required_count": self.review_required_count,
            "average_transition_duration": round(self.average_transition_duration, 4),
            "evidence_completeness_ratio": round(self.evidence_completeness_ratio, 4),
            "duplicate_attempts_count": self.duplicate_attempts_count,
            "integrity_failures_count": self.integrity_failures_count,
            "reliability_score": round(self.reliability_score, 4),
            "failure_category_breakdown": self.failure_category_breakdown,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ReliabilityAnalyzer:
    """Read-only analyzer projecting operational reliability metrics without mutating source records."""

    def __init__(self, observation_tracker: Optional[ExecutionObservationTracker] = None):
        self.tracker = observation_tracker or ExecutionObservationTracker()

    def compute_reliability_from_receipts(
        self,
        receipts: List[ExecutionObservationReceipt],
        duplicate_attempts: int = 0,
        integrity_failures: int = 0
    ) -> OperationalReliabilityRecord:
        """Computes high-fidelity reliability metrics across a collection of observation receipts."""
        total = len(receipts)
        if total == 0:
            return OperationalReliabilityRecord(
                execution_count=0,
                completed_count=0,
                failed_count=0,
                blocked_count=0,
                review_required_count=0,
                average_transition_duration=0.0,
                evidence_completeness_ratio=1.0,
                duplicate_attempts_count=duplicate_attempts,
                integrity_failures_count=integrity_failures,
                reliability_score=1.0 if (duplicate_attempts == 0 and integrity_failures == 0) else 0.0,
                failure_category_breakdown={}
            )

        completed = 0
        failed = 0
        blocked = 0
        review_req = 0
        total_ev_refs = 0
        failure_cats: Dict[str, int] = {}
        durations: List[float] = []

        for r in receipts:
            if r.completion_state == "COMPLETED":
                completed += 1
            elif r.completion_state == "FAILED":
                failed += 1
                cat = r.failure_state or "UNKNOWN_FAILURE"
                failure_cats[cat] = failure_cats.get(cat, 0) + 1
            elif r.completion_state == "HALTED" or "BLOCKED" in str(r.authorization_result):
                blocked += 1
                cat = "BLOCKED_AUTHORIZATION"
                failure_cats[cat] = failure_cats.get(cat, 0) + 1

            if r.authorization_result.get("review_required") or r.completion_state == "REVIEW_REQUIRED":
                review_req += 1

            if r.evidence_references:
                total_ev_refs += 1

            # Extract duration if present in transitions
            for tr in r.observed_transitions:
                if isinstance(tr, dict) and "duration_seconds" in tr:
                    durations.append(float(tr["duration_seconds"]))

        avg_duration = (sum(durations) / len(durations)) if durations else 0.1
        ev_ratio = total_ev_refs / total if total > 0 else 1.0

        # Compute composite reliability score (1.0 = perfect)
        # Deductions for failures, missing evidence, duplicates, and integrity faults
        failure_penalty = (failed * 0.3) + (blocked * 0.2)
        ev_penalty = (1.0 - ev_ratio) * 0.3
        dup_penalty = duplicate_attempts * 0.1
        integrity_penalty = integrity_failures * 0.4

        raw_score = 1.0 - (failure_penalty / max(1, total)) - ev_penalty - dup_penalty - integrity_penalty
        reliability_score = max(0.0, min(1.0, raw_score))

        return OperationalReliabilityRecord(
            execution_count=total,
            completed_count=completed,
            failed_count=failed,
            blocked_count=blocked,
            review_required_count=review_req,
            average_transition_duration=avg_duration,
            evidence_completeness_ratio=ev_ratio,
            duplicate_attempts_count=duplicate_attempts,
            integrity_failures_count=integrity_failures,
            reliability_score=reliability_score,
            failure_category_breakdown=failure_cats
        )

    def analyze_ledger(self) -> OperationalReliabilityRecord:
        """Analyzes the underlying execution observation ledger in a strictly read-only manner."""
        recon = self.tracker.reconstruct_observation_state()
        receipt_data = recon.get("receipts", [])
        receipts = [ExecutionObservationReceipt(**r) for r in receipt_data]
        return self.compute_reliability_from_receipts(receipts)
