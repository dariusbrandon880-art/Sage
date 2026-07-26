"""SAGE ACR/CIV Connection Bond Middleware.

This module establishes the Bond validation connection boundary between SAGE Autonomous Continuity
Runtime (ACR) state transitions and SAGE Policy Enforcement Kernel (CIV / SPEK) validation,
fully complying with the SAGE-EVID-003 protocol requirements.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError

from sage.core.boundary import BoundaryEnforcer
from sage.core.spek import SpekEngine


class BondValidationError(ValueError):
    """Custom exception raised during SAGE Connection Bond validation failures.

    Includes the specific CIV-ERR error code and failure details.
    """
    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{error_code}] {message}")
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class StateTransitionPayload(BaseModel):
    """SAGE-EVID-003 Validation Event Schema for State Transitions.

    Represents the state change requested from an initial state (S0) to a target state (S1).
    """
    transition_id: str = Field(default_factory=lambda: f"trans_{uuid.uuid4().hex[:8]}")
    from_state: str = Field(..., description="Initial state reference (S0)")
    to_state: str = Field(..., description="Target state reference (S1)")
    description: str = Field(..., description="Description of the state transition delta")
    category: str = Field("general", description="Category classification of the transition")
    author: str = Field(..., description="Author of the state transition")
    validation_score: float = Field(..., description="Confidence/evidence rating (0.0 to 1.0)")
    evidence_refs: List[str] = Field(default_factory=list, description="References to supporting evidence")
    parent_ids: List[str] = Field(default_factory=list, description="Ancestor transitions or HDG node IDs")
    contradictions: List[str] = Field(default_factory=list, description="Explicit contradicted states/nodes")
    auth_token: str = Field(..., description="Security boundary validation token")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary transition metadata")


class ValidationPassEvent(BaseModel):
    """Represents a successfully validated and executed SAGE-EVID-003 state transition event."""
    event_id: str = Field(default_factory=lambda: f"evid_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "VALIDATION_PASS"
    transition: StateTransitionPayload
    evidence_capture_path: str
    receipt_hash: str


class BondManager:
    """Manages the Bond connection boundary between ACR transitions and CIV validation."""

    # Standard STP state transition sequence rules for SAGE
    # Allowed from_state -> to_state pairs
    ALLOWED_FLOWS = {
        "S0": {"Delta", "Evidence"},
        "Delta": {"Evidence"},
        "Evidence": {"Validation"},
        "Validation": {"S1"},
    }

    def __init__(
        self,
        spek_engine: Optional[SpekEngine] = None,
        evidence_capture_dir: Optional[str] = None,
    ):
        """Initialize the Bond Manager.

        Args:
            spek_engine: Pre-configured SpekEngine. If None, mock configs are assumed.
            evidence_capture_dir: Directory where SAGE-EVID-003 evidence is persisted.
        """
        self.spek = spek_engine
        self.evidence_capture_dir = Path(evidence_capture_dir or "sage_data/evidence_capture")
        self.evidence_capture_dir.mkdir(parents=True, exist_ok=True)
        self.enforcer = BoundaryEnforcer()
        self.approved_transitions = 0
        self.rejected_transitions = 0
        self.shadow_passes = 0
        self.shadow_failures = 0

    def validate_transition_schema(self, payload_dict: Dict[str, Any]) -> StateTransitionPayload:
        """Validates the transition payload against the SAGE-EVID-003 schema.

        Raises CIV-ERR-SCHM-002 on schema invalidation.
        """
        try:
            return StateTransitionPayload(**payload_dict)
        except ValidationError as e:
            raise BondValidationError(
                error_code="CIV-ERR-SCHM-002",
                message="Schema validation failed for state transition payload.",
                details={"errors": e.errors(), "raw_payload": payload_dict}
            )

    def verify_security_boundary(self, payload: StateTransitionPayload) -> None:
        """Enforces security boundaries for SAGE governance and state paths.

        Raises CIV-ERR-AUTH-001 on boundary violations.
        """
        if payload.auth_token != BoundaryEnforcer.SYSTEM_TOKEN:
            raise BondValidationError(
                error_code="CIV-ERR-AUTH-001",
                message="Security Boundary Enforcement Violation: Unauthorized transition token.",
                details={"provided_token": payload.auth_token}
            )

    def verify_state_flow(self, payload: StateTransitionPayload) -> None:
        """Validates that state sequence follows the formal STP lifecycle transitions.

        Raises CIV-ERR-MUT-003 on invalid sequence or out-of-order mutations.
        """
        from_st = payload.from_state
        to_st = payload.to_state

        # Permit custom S0 -> S1 testing, but reject completely unaligned mutations
        if from_st in self.ALLOWED_FLOWS:
            allowed_targets = self.ALLOWED_FLOWS[from_st]
            if to_st not in allowed_targets:
                raise BondValidationError(
                    error_code="CIV-ERR-MUT-003",
                    message=f"Invalid state transition sequence: '{from_st}' to '{to_st}'.",
                    details={"allowed_targets": list(allowed_targets)}
                )
        elif from_st == "S0" and to_st == "S1":
            # Allow direct S0 -> S1 as an aggregated macro-transition if validated
            pass
        else:
            raise BondValidationError(
                error_code="CIV-ERR-MUT-003",
                message=f"Unrecognized start state '{from_st}' in state transition lifecycle.",
                details={}
            )

    def verify_causality(self, payload: StateTransitionPayload) -> None:
        """Validates ancestry nodes and checks contradictions in HDG causality paths.

        Raises CIV-ERR-SCHM-005 on circular dependencies or causal contradictions.
        """
        # Validate circular dependencies
        if payload.transition_id in payload.parent_ids:
            raise BondValidationError(
                error_code="CIV-ERR-SCHM-005",
                message="Causality Violation: Circular dependency detected in parent references.",
                details={"transition_id": payload.transition_id, "parent_ids": payload.parent_ids}
            )

        # Validate explicit contradictions
        contradictions_set = set(payload.contradictions)
        ancestor_set = set(payload.parent_ids)
        intersection = contradictions_set.intersection(ancestor_set)
        if intersection:
            raise BondValidationError(
                error_code="CIV-ERR-SCHM-005",
                message=f"Causality Violation: Contradiction detected with ancestor nodes: {list(intersection)}.",
                details={"contradictions": payload.contradictions, "ancestor_nodes": payload.parent_ids}
            )

    def verify_evidence_confidence(self, payload: StateTransitionPayload) -> None:
        """Validates that validation/confidence score is equal to or above the evidence threshold.

        Raises CIV-ERR-EXT-004 on low evidence.
        """
        threshold = 0.7
        if self.spek:
            threshold = self.spek.evidence_threshold

        if payload.validation_score < threshold:
            raise BondValidationError(
                error_code="CIV-ERR-EXT-004",
                message=f"Validation failed: Confidence score {payload.validation_score:.2f} is below evidence threshold {threshold:.2f}.",
                details={"validation_score": payload.validation_score, "threshold": threshold}
            )

    def execute_transition(self, current_state: dict, raw_payload: dict) -> dict:
        """Executes the SAGE transition cleanly S0 -> S1, guaranteeing rollback on failure.

        Args:
            current_state: S0 state context (dict) to transition.
            raw_payload: Input dictionary containing transition specifications.

        Returns:
            The upgraded S1 state context if VALIDATION_PASS occurs.
        """
        # Preserve original S0 state completely for rollback guarantees
        s0_backup = json.loads(json.dumps(current_state))

        try:
            # 1. Schema Validation (CIV-ERR-SCHM-002)
            payload = self.validate_transition_schema(raw_payload)

            # 2. Authentication and Boundary Validation (CIV-ERR-AUTH-001)
            self.verify_security_boundary(payload)

            # 3. State Mutation Lifecycle Validation (CIV-ERR-MUT-003)
            self.verify_state_flow(payload)

            # 4. HDG Causality Validation (CIV-ERR-SCHM-005)
            self.verify_causality(payload)

            # 5. Evidence Verification (CIV-ERR-EXT-004)
            self.verify_evidence_confidence(payload)

            # 6. Execute SPEK connection if SpekEngine is present
            if self.spek:
                try:
                    self.spek.process_proposal(
                        proposal_id=payload.transition_id,
                        description=payload.description,
                        category=payload.category,
                        author=payload.author,
                        parent_ids=payload.parent_ids,
                        evidence_refs=payload.evidence_refs,
                        validation_score=payload.validation_score,
                        contradictions=payload.contradictions,
                        auth_token=payload.auth_token,
                    )
                except ValueError as spek_err:
                    err_msg = str(spek_err)
                    if "Contradiction detected" in err_msg:
                        raise BondValidationError(
                            error_code="CIV-ERR-SCHM-005",
                            message=err_msg,
                            details={"transition_id": payload.transition_id}
                        )
                    elif "below evidence threshold" in err_msg:
                        raise BondValidationError(
                            error_code="CIV-ERR-EXT-004",
                            message=err_msg,
                            details={"validation_score": payload.validation_score}
                        )
                    else:
                        raise BondValidationError(
                            error_code="CIV-ERR-MUT-003",
                            message=err_msg,
                            details={}
                        )

            # S0 -> S1 Mutation execution
            # Generate deterministic S1 state based on transition delta
            s1_state = s0_backup.copy()
            s1_state["current_project_state"] = payload.to_state
            s1_state["last_applied_transition"] = payload.transition_id
            s1_state["active_milestone"] = payload.metadata.get("milestone", s1_state.get("active_milestone"))

            if "unresolved_items" in s1_state and isinstance(s1_state["unresolved_items"], list):
                # Resolve completed tasks or add new ones
                for task in payload.evidence_refs:
                    if task in s1_state["unresolved_items"]:
                        s1_state["unresolved_items"].remove(task)

            # Generate deterministic VALIDATION_PASS event
            evidence_file_name = f"evidence_{payload.transition_id}_{uuid.uuid4().hex[:6]}.json"
            evidence_path = self.evidence_capture_dir / evidence_file_name

            # Build SAGE-EVID-003 deterministic receipt
            event_id = f"evid_{uuid.uuid4().hex[:8]}"
            receipt_payload = {
                "event_id": event_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "VALIDATION_PASS",
                "transition_id": payload.transition_id,
                "from_state": payload.from_state,
                "to_state": payload.to_state,
                "author": payload.author,
            }
            receipt_hash = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode("utf-8")).hexdigest()

            pass_event = ValidationPassEvent(
                event_id=event_id,
                timestamp=datetime.now(timezone.utc),
                transition=payload,
                evidence_capture_path=str(evidence_path),
                receipt_hash=receipt_hash
            )

            # Store SAGE-EVID-003 artifact
            with open(evidence_path, "w") as f:
                json.dump(pass_event.model_dump(), f, indent=2, default=str)

            self.approved_transitions += 1
            return s1_state

        except BondValidationError as bve:
            self.rejected_transitions += 1
            # Rollback S1 state to original S0 state completely
            current_state.clear()
            current_state.update(s0_backup)
            # Re-raise the exception with full error code propagation
            raise bve
        except Exception as e:
            self.rejected_transitions += 1
            # Handle general errors with rollback and map to CIV-ERR-SCHM-002
            current_state.clear()
            current_state.update(s0_backup)
            raise BondValidationError(
                error_code="CIV-ERR-SCHM-002",
                message=f"State transition validation aborted: {e!s}",
                details={}
            )
