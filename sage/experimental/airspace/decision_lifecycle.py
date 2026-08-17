"""SAGE Decision Lifecycle Observation Engine.

Observes whether a previously generated OperationalDecisionBoundary package
remains valid over time or after new evidence, state changes, or time elapsed,
answering: "Was this decision package still valid?"
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.airspace.decision_boundary import (
    DecisionRecommendation,
    OperationalDecisionBoundary,
    OperationalDecisionBoundaryEvaluator,
)
from sage.experimental.airspace.readiness import OperationalReadinessAssessment, ReadinessStatus


class DecisionValidityState(str, Enum):
    """Lifecycle validity states for a decision package."""
    DECISION_CREATED = "DECISION_CREATED"
    DECISION_VALIDATED = "DECISION_VALIDATED"
    DECISION_STALE = "DECISION_STALE"
    DECISION_CONFLICTED = "DECISION_CONFLICTED"
    DECISION_REVIEW_REQUIRED = "DECISION_REVIEW_REQUIRED"


class DecisionLifecycleRecord(BaseModel):
    """Observation record tracking the temporal validity and lifecycle state of a decision package."""
    decision_id: str
    created_timestamp: str
    source_decision_reference: str
    evidence_snapshot_reference: List[str] = Field(default_factory=list)
    validity_state: DecisionValidityState = DecisionValidityState.DECISION_CREATED
    validation_events: List[Dict[str, Any]] = Field(default_factory=list)
    invalidation_reasons: List[str] = Field(default_factory=list)
    review_required: bool = False
    integrity_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.integrity_hash:
            self.integrity_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        serialized = json.dumps({
            "decision_id": self.decision_id,
            "created_timestamp": self.created_timestamp,
            "source_decision_reference": self.source_decision_reference,
            "evidence_snapshot_reference": sorted(self.evidence_snapshot_reference),
            "validity_state": self.validity_state.value,
            "invalidation_reasons": self.invalidation_reasons,
            "review_required": self.review_required,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class DecisionLifecycleObserver:
    """Read-only observer evaluating decision validity over time and state transitions."""

    def __init__(
        self,
        decision_evaluator: Optional[OperationalDecisionBoundaryEvaluator] = None,
        max_validity_hours: float = 24.0,
    ):
        self.decision_evaluator = decision_evaluator or OperationalDecisionBoundaryEvaluator()
        self.max_validity_hours = max_validity_hours

    def observe_decision_lifecycle(
        self,
        source_boundary: OperationalDecisionBoundary,
        current_boundary: Optional[OperationalDecisionBoundary] = None,
        session_id: Optional[str] = None,
    ) -> DecisionLifecycleRecord:
        """Observes the validity state of source_boundary against current operational state."""
        # Query current decision boundary if not provided
        latest_boundary = current_boundary or self.decision_evaluator.evaluate_decision_boundary(session_id=session_id)

        invalidation_reasons = []
        validation_events = []
        review_required = False
        validity_state = DecisionValidityState.DECISION_VALIDATED

        now_utc = datetime.now(timezone.utc)

        # 1. Temporal Staleness Check
        try:
            created_dt = datetime.fromisoformat(source_boundary.timestamp)
            if now_utc - created_dt > timedelta(hours=self.max_validity_hours):
                validity_state = DecisionValidityState.DECISION_STALE
                invalidation_reasons.append(f"Decision created at {source_boundary.timestamp} exceeds max validity TTL ({self.max_validity_hours}h)")
                review_required = True
        except Exception:
            pass

        # 2. Latest Readiness Status Check
        if latest_boundary.readiness_reference == ReadinessStatus.STALE_OBSERVATION.value:
            validity_state = DecisionValidityState.DECISION_STALE
            invalidation_reasons.append(f"Latest observation telemetry is stale: {latest_boundary.rationale}")
            review_required = True
        elif latest_boundary.readiness_reference == ReadinessStatus.REQUIRES_REVIEW_CONFLICT.value:
            validity_state = DecisionValidityState.DECISION_CONFLICTED
            invalidation_reasons.append(f"Subsystem conflict detected: {latest_boundary.rationale}")
            review_required = True
        elif latest_boundary.readiness_reference == ReadinessStatus.BLOCKED_MISSING_EVIDENCE.value:
            validity_state = DecisionValidityState.DECISION_REVIEW_REQUIRED
            invalidation_reasons.append(f"Missing evidence blocks decision validity: {latest_boundary.rationale}")
            review_required = True

        # 3. Evidence Snapshot Drift Check
        if sorted(source_boundary.supporting_evidence) != sorted(latest_boundary.supporting_evidence):
            if validity_state == DecisionValidityState.DECISION_VALIDATED:
                validity_state = DecisionValidityState.DECISION_REVIEW_REQUIRED
            invalidation_reasons.append("Evidence snapshot drift detected: New evidence artifacts registered since decision creation")
            review_required = True

        # Log validation event
        validation_events.append({
            "observed_at": now_utc.isoformat(),
            "source_recommendation": source_boundary.decision_recommendation.value,
            "current_recommendation": latest_boundary.decision_recommendation.value,
            "resulting_validity_state": validity_state.value,
            "review_required": review_required,
        })

        return DecisionLifecycleRecord(
            decision_id=f"LIFECYCLE-{source_boundary.decision_id}",
            created_timestamp=source_boundary.timestamp,
            source_decision_reference=source_boundary.decision_id,
            evidence_snapshot_reference=source_boundary.supporting_evidence,
            validity_state=validity_state,
            validation_events=validation_events,
            invalidation_reasons=invalidation_reasons,
            review_required=review_required,
        )
