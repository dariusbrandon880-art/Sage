"""Governed Decision Boundary Engine for SAGE Airspace.

Produces auditable decision packages from Operational Readiness Assessments,
explaining what is known, what is unknown, what evidence supports continuation,
what blocks continuation, and what requires authorization before advancing frontiers.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.airspace.readiness import (
    OperationalReadinessAssessment,
    OperationalReadinessEvaluator,
    ReadinessStatus,
)


class DecisionRecommendation(str, Enum):
    """SAGE Governed Decision Recommendation."""
    PROCEED_AUTHORIZED_FRONTIER = "PROCEED_AUTHORIZED_FRONTIER"
    HOLD_MISSING_EVIDENCE = "HOLD_MISSING_EVIDENCE"
    HOLD_CONFLICT_REVIEW = "HOLD_CONFLICT_REVIEW"
    HOLD_CORRUPTED_STATE = "HOLD_CORRUPTED_STATE"
    HOLD_STALE_OBSERVATION = "HOLD_STALE_OBSERVATION"


class OperationalDecisionBoundary(BaseModel):
    """Auditable decision package representing SAGE decision readiness."""
    decision_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    readiness_reference: str
    supporting_evidence: List[str] = Field(default_factory=list)
    active_conditions: Dict[str, Any] = Field(default_factory=dict)
    verified_conditions: Dict[str, Any] = Field(default_factory=dict)
    blocking_conditions: Dict[str, Any] = Field(default_factory=dict)
    unknown_conditions: Dict[str, Any] = Field(default_factory=dict)
    authorization_required: Dict[str, Any] = Field(default_factory=dict)
    recommended_frontier: str = ""
    decision_recommendation: DecisionRecommendation = DecisionRecommendation.HOLD_MISSING_EVIDENCE
    rationale: str = ""


class OperationalDecisionBoundaryEvaluator:
    """Evaluates readiness assessments to project auditable decision packages."""

    def __init__(
        self,
        readiness_evaluator: Optional[OperationalReadinessEvaluator] = None,
        airspace_ledger_path: Optional[str | Path] = None,
        act_storage_path: Optional[str | Path] = None,
        sports_ledger_path: Optional[str | Path] = None,
    ):
        self.readiness_evaluator = readiness_evaluator or OperationalReadinessEvaluator(
            airspace_ledger_path=airspace_ledger_path,
            act_storage_path=act_storage_path,
            sports_ledger_path=sports_ledger_path,
        )

    def evaluate_decision_boundary(self, session_id: Optional[str] = None) -> OperationalDecisionBoundary:
        """Generates an auditable OperationalDecisionBoundary from current persistent state."""
        assessment = self.readiness_evaluator.evaluate_readiness(session_id=session_id)
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%Y%m%d")
        dec_id = f"DEC-BOUND-{date_str}-{hashlib.sha256(f'{assessment.timestamp}:{assessment.readiness_status}'.encode('utf-8')).hexdigest()[:8]}"

        # Supporting evidence extraction
        supporting_evidence = []
        if isinstance(assessment.verified, dict) and "evidence_count" in assessment.verified:
            airspace_state = self.readiness_evaluator.resolver.airspace_manager.reconstruct_airspace_state()
            supporting_evidence = airspace_state.recent_evidence

        # Active, Verified, Blocking, Unknown conditions
        active_conds = assessment.active
        verified_conds = assessment.verified
        blocking_conds = assessment.blocked

        unknown_conds = {
            "unresolved_sports_predictions": assessment.active.get("unresolved_sports_predictions", 0),
            "untracked_external_dependencies": "None detected",
        }

        # Determine Recommendation, Rationale, and Authorization
        if assessment.readiness_status == ReadinessStatus.READY:
            recommendation = DecisionRecommendation.PROCEED_AUTHORIZED_FRONTIER
            rationale = "Persistent evidence is complete and verified across ACT, Airspace, and Sports/RCE. Ready for human authorization to advance frontier."
            recommended_frontier = assessment.authorized_next.get("frontier", "Advance to next authorized milestone")
            auth_required = {
                "clearance_authority": "MISSION_DIRECTOR (Human Operator)",
                "required_action": "Review decision package and grant frontier authorization",
                "zero_spawning_enforced": True,
            }
        elif assessment.readiness_status == ReadinessStatus.BLOCKED_MISSING_EVIDENCE:
            recommendation = DecisionRecommendation.HOLD_MISSING_EVIDENCE
            rationale = f"Decision hold enforced: {assessment.evaluation_reason}"
            recommended_frontier = "HOLD at current boundary until missing evidence is provided"
            auth_required = {
                "clearance_authority": "MISSION_DIRECTOR / ENGINEERING_FLIGHT",
                "required_action": "Provide missing evidence references before requesting clearance",
                "zero_spawning_enforced": True,
            }
        elif assessment.readiness_status == ReadinessStatus.REQUIRES_REVIEW_CONFLICT:
            recommendation = DecisionRecommendation.HOLD_CONFLICT_REVIEW
            rationale = f"Decision hold enforced: {assessment.evaluation_reason}"
            recommended_frontier = "HOLD at current boundary until cross-system state conflict is reconciled"
            auth_required = {
                "clearance_authority": "MISSION_DIRECTOR (Human Operator)",
                "required_action": "Manual review and reconciliation of conflicting subsystem states",
                "zero_spawning_enforced": True,
            }
        elif assessment.readiness_status == ReadinessStatus.STATE_CORRUPTED:
            recommendation = DecisionRecommendation.HOLD_CORRUPTED_STATE
            rationale = f"Decision hold enforced: {assessment.evaluation_reason}"
            recommended_frontier = "HALT execution loop and repair persistent state ledger"
            auth_required = {
                "clearance_authority": "ENGINEERING_FLIGHT",
                "required_action": "Inspect and restore corrupted state ledger file",
                "zero_spawning_enforced": True,
            }
        else:  # STALE_OBSERVATION
            recommendation = DecisionRecommendation.HOLD_STALE_OBSERVATION
            rationale = f"Decision hold enforced: {assessment.evaluation_reason}"
            recommended_frontier = "Refresh observation telemetry from active environment"
            auth_required = {
                "clearance_authority": "INTEL_STATION / ENGINEERING_FLIGHT",
                "required_action": "Execute fresh observation telemetry cycle",
                "zero_spawning_enforced": True,
            }

        return OperationalDecisionBoundary(
            decision_id=dec_id,
            timestamp=now_utc.isoformat(),
            readiness_reference=assessment.readiness_status.value,
            supporting_evidence=supporting_evidence,
            active_conditions=active_conds,
            verified_conditions=verified_conds,
            blocking_conditions=blocking_conds,
            unknown_conditions=unknown_conds,
            authorization_required=auth_required,
            recommended_frontier=recommended_frontier,
            decision_recommendation=recommendation,
            rationale=rationale,
        )
