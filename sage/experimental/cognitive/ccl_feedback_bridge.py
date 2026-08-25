"""Cognitive Causal Learning (CCL) Outcome Feedback Bridge."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine


class CCLFeedbackRecord(BaseModel):
    """Immutable feedback record produced by CCL Outcome Feedback Bridge."""

    record_id: str
    mission_id: str
    frontier_id: str
    target_namespace: str
    outcome_status: str  # PASS, FAIL, DRIFT_DETECTED
    causal_attribution: Dict[str, Any] = Field(default_factory=dict)
    feedback_timestamp: float = Field(default_factory=time.time)
    record_hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint for feedback record."""
        payload = {
            "record_id": self.record_id,
            "mission_id": self.mission_id,
            "frontier_id": self.frontier_id,
            "target_namespace": self.target_namespace,
            "outcome_status": self.outcome_status,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class CCLOutcomeFeedbackBridge:
    """Connects execution outcome reconciliation with Adaptive Mission Selection Engine for 2-cycle feedback compounding."""

    def __init__(self, selection_engine: Optional[AdaptiveMissionSelectionEngine] = None):
        self.selection_engine = selection_engine or AdaptiveMissionSelectionEngine()
        self.feedback_history: List[CCLFeedbackRecord] = []

    def process_outcome(
        self,
        mission_id: str,
        frontier_id: str,
        target_namespace: str,
        outcome_status: str,
        causal_attribution: Optional[Dict[str, Any]] = None,
    ) -> CCLFeedbackRecord:
        """Process an execution outcome and record failure history if outcome indicates failure or drift."""
        attribution = causal_attribution or {}
        record_id = f"ccl-fb-{mission_id}-{time.time_ns()}"

        record = CCLFeedbackRecord(
            record_id=record_id,
            mission_id=mission_id,
            frontier_id=frontier_id,
            target_namespace=target_namespace,
            outcome_status=outcome_status,
            causal_attribution=attribution,
        )
        record.record_hash = record.compute_hash()
        self.feedback_history.append(record)
        return record

    def get_failure_history(self) -> List[Dict[str, Any]]:
        """Extract failure history records formatted for AdaptiveMissionSelectionEngine consumption."""
        failures = []
        for r in self.feedback_history:
            if r.outcome_status in {"FAIL", "DRIFT_DETECTED"}:
                failures.append({
                    "mission_id": r.mission_id,
                    "frontier_id": r.frontier_id,
                    "target_namespace": r.target_namespace,
                    "status": r.outcome_status,
                })
        return failures
