"""SAGE Governed Mission Intake Layer.

Accepts proposed missions, validates their structural and metadata requirements,
evaluates prerequisite dependencies, and registers them into the MISSION_PROPOSED state
under strict sequential governance with default unapproved authorization gates.
"""

import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from sage.mission_control import ExperimentalMissionState, SAGEMissionProgressionController


class MissionProposal(BaseModel):
    """Schema representing an inbound proposed mission for SAGE."""
    name: str = Field(..., description="Short name of the proposed mission")
    description: str = Field(..., description="Vivid description of purpose")
    objective: str = Field(..., description="Objective statement of the mission")
    operator_id: str = Field(..., description="The supervisor/operator proposing the mission")
    provenance_ref: Optional[str] = Field(
        default=None,
        description="Source evidence or discovery signal provenance reference"
    )
    prerequisites: Dict[str, bool] = Field(
        default_factory=dict,
        description="Satisfied prerequisites mapped at proposal time"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary custom metadata fields"
    )


class ProposalRejectionRecord(BaseModel):
    """Record of a structurally invalid or rejected mission proposal."""
    proposal_data: Dict[str, Any] = Field(..., description="The raw input proposal data")
    rejection_reason: str = Field(..., description="Explanation of why validation failed")
    timestamp: float = Field(..., description="Epoch timestamp of the rejection")


class SAGEMissionIntakeLayer:
    """Intake gateway validating mission proposals, checking prerequisites, and maintaining queue."""

    def __init__(self) -> None:
        self.queue: List[ExperimentalMissionState] = []
        self.rejections: List[ProposalRejectionRecord] = []
        self.controller = SAGEMissionProgressionController()

    def generate_deterministic_id(self, name: str, operator_id: str, timestamp: float) -> str:
        """Create a cryptographically deterministic mission ID using SHA-256."""
        seed_string = f"{name}:{operator_id}:{timestamp}"
        sha = hashlib.sha256(seed_string.encode("utf-8")).hexdigest()
        return f"msn-intake-{sha[:16]}"

    def submit_proposal(
        self,
        proposal: Dict[str, Any],
        *,
        authorized_candidate_ids: Optional[Tuple[str, ...]] = None,
    ) -> Dict[str, Any]:
        """Accept and validate an inbound mission proposal.

        Enforces strict structural rules, dependency prerequisite checks,
        default unauthorized authorization gates, and enqueues accepted missions
        strictly in the MISSION_PROPOSED state.
        """
        timestamp = time.time()

        # 1. Structural and field validation
        required_fields = ["name", "description", "objective", "operator_id"]
        missing_fields = [f for f in required_fields if f not in proposal or not proposal[f]]

        if missing_fields:
            reason = f"Rejection: Missing required fields: {', '.join(missing_fields)}"
            self.rejections.append(
                ProposalRejectionRecord(
                    proposal_data=proposal,
                    rejection_reason=reason,
                    timestamp=timestamp
                )
            )
            return {
                "accepted": False,
                "status": "REJECTED",
                "reason": reason
            }

        # 2. Check for empty strings in required fields
        for field in required_fields:
            if not str(proposal[field]).strip():
                reason = f"Rejection: Field '{field}' cannot be empty or blank."
                self.rejections.append(
                    ProposalRejectionRecord(
                        proposal_data=proposal,
                        rejection_reason=reason,
                        timestamp=timestamp
                    )
                )
                return {
                    "accepted": False,
                    "status": "REJECTED",
                    "reason": reason
                }

        # 3. Create validated MissionProposal
        try:
            validated = MissionProposal(**proposal)
        except Exception as e:
            reason = f"Rejection: Schema validation failed: {e!s}"
            self.rejections.append(
                ProposalRejectionRecord(
                    proposal_data=proposal,
                    rejection_reason=reason,
                    timestamp=timestamp
                )
            )
            return {
                "accepted": False,
                "status": "REJECTED",
                "reason": reason
            }

        # 4. Dependency prerequisite check: Any explicitly listed prerequisite set to False fails intake
        unfulfilled_prereqs = [req for req, satisfied in validated.prerequisites.items() if not satisfied]
        if unfulfilled_prereqs:
            reason = f"Rejection: Unfulfilled prerequisite dependencies: {', '.join(unfulfilled_prereqs)}"
            self.rejections.append(
                ProposalRejectionRecord(
                    proposal_data=proposal,
                    rejection_reason=reason,
                    timestamp=timestamp
                )
            )
            return {
                "accepted": False,
                "status": "REJECTED",
                "reason": reason,
                "unfulfilled_prerequisites": unfulfilled_prereqs,
            }

        # 5. Generate deterministic ID & preserve provenance
        mission_id = self.generate_deterministic_id(validated.name, validated.operator_id, timestamp)

        # Authorization Gate Check: Defaults to False unless candidate ID is in authorized set
        candidate_id = proposal.get("candidate_id") or proposal.get("metadata", {}).get("candidate_id")
        is_authorized = False
        if candidate_id and authorized_candidate_ids and candidate_id in authorized_candidate_ids:
            is_authorized = True

        # Build initial governed mission state strictly in MISSION_PROPOSED
        mission_state = ExperimentalMissionState(
            mission_id=mission_id,
            name=validated.name,
            current_state="MISSION_PROPOSED",
            prerequisites=validated.prerequisites,
            metadata={
                "description": validated.description,
                "objective": validated.objective,
                "authorized": is_authorized,
                "provenance_ref": validated.provenance_ref or proposal.get("provenance_ref"),
                "provenance": {
                    "operator_id": validated.operator_id,
                    "timestamp": timestamp,
                    "original_proposal": proposal,
                }
            }
        )

        # 6. Maintain deterministic queue order (FIFO enqueue)
        self.queue.append(mission_state)

        return {
            "accepted": True,
            "status": "ACCEPTED",
            "mission_id": mission_id,
            "current_state": "MISSION_PROPOSED",
            "authorized": is_authorized,
            "queue_position": len(self.queue) - 1
        }

    def handoff_to_controller(self, mission_id: str, target_state: str) -> Dict[str, Any]:
        """Hand off an accepted mission state to the existing Mission Progression Controller.

        Ensures that the intake layer itself never authorizes execution or advances
        beyond the MISSION_PROPOSED stage independently.
        """
        # Find mission in queue
        mission_state = next((m for m in self.queue if m.mission_id == mission_id), None)
        if not mission_state:
            return {
                "success": False,
                "reason": f"Mission '{mission_id}' not found in intake queue."
            }

        # Evaluate transition via existing controller
        result = self.controller.evaluate_transition(mission_state, target_state)
        return result.model_dump()

    def get_queue(self) -> List[ExperimentalMissionState]:
        """Return the current enqueued mission states in FIFO order."""
        return list(self.queue)

    def get_rejections(self) -> List[ProposalRejectionRecord]:
        """Return the audit log of rejected proposals."""
        return list(self.rejections)
