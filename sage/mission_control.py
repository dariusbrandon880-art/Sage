"""SAGE Mission Progression Controller - Governed State-Transition Mechanism.

Evaluates whether a queued mission may advance to its next governed state
through strict validation of prerequisites and sequence boundaries.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# 1. Represent the controlled lifecycle stages in strict sequential order
LIFECYCLE_SEQUENCE = [
    "MISSION_PROPOSED",
    "VALUE_EVALUATED",
    "PREFLIGHT_REQUIRED",
    "EXECUTION_AUTHORIZED",
    "EXECUTION_COMPLETE",
    "VALIDATION_REQUIRED",
    "EVIDENCE_REQUIRED",
    "REVIEW_REQUIRED",
    "PROMOTION_READY",
    "CLOSED"
]

# 2. Map target transition states to their required prerequisite keys
PREREQUISITES_MAP = {
    "VALUE_EVALUATED": "value_appraisal_approved",
    "PREFLIGHT_REQUIRED": "preflight_checklist_passed",
    "EXECUTION_AUTHORIZED": "operator_signature_obtained",
    "EXECUTION_COMPLETE": "execution_log_recorded",
    "VALIDATION_REQUIRED": "validation_receipt_issued",
    "EVIDENCE_REQUIRED": "evidence_hashes_verified",
    "REVIEW_REQUIRED": "peer_signoff_completed",
    "PROMOTION_READY": "promotion_approval_granted",
    "CLOSED": "archival_success_confirmed"
}


class ExperimentalMissionState(BaseModel):
    """Structured representing the current state and parameters of a SAGE mission."""
    mission_id: str = Field(..., description="Unique identifier for the mission")
    name: str = Field(..., description="Human-readable name of the mission")
    current_state: str = Field("MISSION_PROPOSED", description="Active lifecycle stage")
    prerequisites: Dict[str, bool] = Field(
        default_factory=dict,
        description="Satisfied prerequisite checks for transitioning stages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata supporting the mission state"
    )


class MissionTransitionResult(BaseModel):
    """Structured outcome of a mission progression evaluation."""
    success: bool = Field(..., description="Whether the transition was accepted and processed")
    transitioned: bool = Field(..., description="True if state moved to target stage")
    previous_state: str = Field(..., description="The state prior to the evaluation request")
    target_state: str = Field(..., description="The evaluated destination state")
    decision_reason: str = Field(..., description="Detailed explanation of the accept/reject outcome")
    explainable_trace: Dict[str, str] = Field(
        default_factory=dict,
        description="Standard explanation mapping for auditability"
    )


class SAGEMissionProgressionController:
    """Deterministic state-transition mechanism evaluating SAGE mission progressions.

    Enforces that missions advance strictly in sequential order, requiring
    documented prerequisites to be satisfied, and guarantees no autonomous
    code execution or database/archive side effects can occur.
    """

    def __init__(self) -> None:
        pass

    def evaluate_transition(
        self,
        mission_state: ExperimentalMissionState,
        target_state: str
    ) -> MissionTransitionResult:
        """Evaluate if the given mission is allowed to advance to the target state.

        Performs sequence validation, prerequisite checks, and enforces
        Proposal Non-Execution and Zero-Self-Authorization laws.
        """
        current_state = mission_state.current_state

        # Validate that the states are valid lifecycle stages
        if current_state not in LIFECYCLE_SEQUENCE:
            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason=f"Current state '{current_state}' is not a valid SAGE lifecycle stage."
            )

        if target_state not in LIFECYCLE_SEQUENCE:
            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason=f"Target state '{target_state}' is not a valid SAGE lifecycle stage."
            )

        # Enforce terminal state boundary: once CLOSED, no further transitions are allowed
        if current_state == "CLOSED":
            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason="Mission is in terminal CLOSED state. No further transitions are permitted."
            )

        # Enforce strict sequential order: target state must be the exact direct successor
        current_index = LIFECYCLE_SEQUENCE.index(current_state)
        target_index = LIFECYCLE_SEQUENCE.index(target_state)

        if target_index != current_index + 1:
            if target_index == current_index:
                return MissionTransitionResult(
                    success=True,
                    transitioned=False,
                    previous_state=current_state,
                    target_state=target_state,
                    decision_reason="No transition requested; state remains unchanged."
                )

            # Identify if transition skipped stages or went backward
            if target_index > current_index + 1:
                reason = f"Invalid transition: Cannot skip sequential stages (requested {current_state} -> {target_state})."
            else:
                reason = f"Invalid transition: Backward progression is forbidden (requested {current_state} -> {target_state})."

            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason=reason
            )

        # Enforce prerequisite check: the required prerequisite for the target state must be satisfied
        required_prereq = PREREQUISITES_MAP.get(target_state)
        if not required_prereq:
            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason=f"Technical error: No prerequisite mapped for target state '{target_state}'."
            )

        prereq_satisfied = mission_state.prerequisites.get(required_prereq, False)
        if not prereq_satisfied:
            return MissionTransitionResult(
                success=False,
                transitioned=False,
                previous_state=current_state,
                target_state=target_state,
                decision_reason=f"Blocked: Missing prerequisite '{required_prereq}' for transition to '{target_state}'."
            )

        # Proposal Non-Execution Law: Ensure the controller performs no execution itself
        # Zero Self-Authorization Law: Controller never grants itself or changes any authorization automatically
        explainable_trace = {
            "mission_id": mission_state.mission_id,
            "prerequisite_required": required_prereq,
            "decision": "ACCEPTED",
            "evidence_state": f"Prerequisite {required_prereq} is satisfied (True).",
            "next_allowed_state": target_state
        }

        # Apply state mutation to the input mission_state if approved
        mission_state.current_state = target_state

        return MissionTransitionResult(
            success=True,
            transitioned=True,
            previous_state=current_state,
            target_state=target_state,
            decision_reason=f"Transition to '{target_state}' successfully authorized.",
            explainable_trace=explainable_trace
        )
