"""SAGE Capability Passport Governance Engine (SAGE-CPGE) - Section 2.

Implements the Capability Passport Model, the No Orphan Capability Rule,
and Capability State Transition Records to prevent rogue or undocumented capabilities
under the SAGE Capability Evolution Governance Framework.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CapabilityPassport(BaseModel):
    """Immutable representation of a SAGE Capability Passport under Section 2.1."""

    name: str = Field(..., description="Unique structured capability name (e.g., CAP-SAGE-ACT)")
    purpose: str = Field(..., description="High-fidelity statement of problem solved")
    lifecycle_state: str = Field("PROPOSED", description="PROPOSED, VALIDATED, ARCHIVE_CANDIDATE, CANONICAL")
    dependencies: List[str] = Field(default_factory=list)
    validation_strategy: str = Field(..., description="Testing/observation protocol used to gather proof")
    evidence_path: str = Field(..., description="Staging path where evidence is stored")
    archive_location: str = Field(..., description="INDEX.md entry reference")
    reviewer_decision: str = Field("Pending", description="Approved, Pending, Revision Required")
    allowed_next_state: str = Field("VALIDATED", description="Permitted state transition target")

    @field_validator("name")
    @classmethod
    def validate_capability_name(cls, v: str) -> str:
        """Enforce CAP- prefix and structured format."""
        if not re.match(r"^CAP-[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"SAGE Passport Violation: Name must start with 'CAP-' prefix. Found: '{v}'")
        return v

    @field_validator("lifecycle_state")
    @classmethod
    def validate_lifecycle_state(cls, v: str) -> str:
        """Enforce strict lifecycle transitions."""
        valid_states = {"PROPOSED", "VALIDATED", "ARCHIVE_CANDIDATE", "CANONICAL"}
        if v not in valid_states:
            raise ValueError(f"SAGE Passport Violation: Invalid lifecycle_state: '{v}'")
        return v


class CapabilityStateTransitionRecord(BaseModel):
    """Immutable representation of a Capability State Transition under Section 3.1."""

    capability_name: str
    current_state: str
    validation_strategy: str
    evidence_package_id: str
    reviewer_decision: str
    next_allowed_state: str


class CapabilityPassportGovernanceEngine:
    """Enforces the 'No Orphan Capability Rule' and manages capability state transitions."""

    def __init__(self, validation_mode: str = "strict"):
        self.validation_mode = validation_mode

    def verify_no_orphan_rule(self, passport: CapabilityPassport) -> bool:
        """Enforces the No Orphan Capability Rule (Section 2.2).

        A capability is classified as an orphan if it lacks:
        - A non-empty Name
        - A non-empty Purpose
        - A clear Lifecycle State
        - A defined Validation Strategy
        - A designated Evidence Path
        - A registered Archive Location/reference
        """
        # Ensure none of the core fields are missing or whitespace-only
        if not passport.name or not passport.name.strip():
            return False
        if not passport.purpose or not passport.purpose.strip():
            return False
        if not passport.lifecycle_state or not passport.lifecycle_state.strip():
            return False
        if not passport.validation_strategy or not passport.validation_strategy.strip():
            return False
        if not passport.evidence_path or not passport.evidence_path.strip():
            return False
        if not passport.archive_location or not passport.archive_location.strip():
            return False

        # Verify formatting invariants
        if not passport.evidence_path.endswith(".json"):
            return False
        if not passport.archive_location.endswith(".md"):
            return False

        return True

    def process_state_transition(
        self,
        passport: CapabilityPassport,
        evidence_package_id: str,
        reviewer_decision: str
    ) -> CapabilityStateTransitionRecord:
        """Validates and transition capability states under Section 3."""
        # Check No Orphan Rule first
        if not self.verify_no_orphan_rule(passport):
            raise ValueError(f"SAGE Passport Violation: Capability '{passport.name}' fails the 'No Orphan Capability Rule'.")

        if reviewer_decision == "Approved":
            next_state = passport.allowed_next_state
        elif reviewer_decision == "Revision Required":
            next_state = "PROPOSED"
        else:
            next_state = passport.lifecycle_state

        record = CapabilityStateTransitionRecord(
            capability_name=passport.name,
            current_state=passport.lifecycle_state,
            validation_strategy=passport.validation_strategy,
            evidence_package_id=evidence_package_id,
            reviewer_decision=reviewer_decision,
            next_allowed_state=next_state
        )

        return record
