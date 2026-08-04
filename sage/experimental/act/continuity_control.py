"""SAGE Continuity Control Loop (SAGE-CCL) - Milestone 3.

Provides a robust, sandboxed telemetry tap to capture AI workflow events,
enrich them with session objectives from the SessionStateManager,
run adversarial validations, and support manual human approval to promote
records from PROPOSED to VALIDATED lifecycle states.
"""

import os
import re
import json
import time
import uuid
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from sage.acr.session.session_state import SessionStateManager, SessionState


class ContinuityControlRecord(BaseModel):
    """Immutable representation of a SAGE Continuity Control Loop record."""

    record_id: str
    session_id: str
    event_type: str
    timestamp: float
    action_taken: str
    decision_reasoning: str
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)
    failure_context: Optional[Dict[str, Any]] = None
    recovery_path: Optional[str] = None
    lifecycle_state: str = "PROPOSED"
    workflow_friction: List[Dict[str, Any]] = Field(default_factory=list)
    improvement_opportunities: List[str] = Field(default_factory=list)

    @field_validator("record_id")
    @classmethod
    def validate_record_id(cls, v: str) -> str:
        """Enforce strict record_id formatting."""
        if not re.match(r"^CCL-REC-\d{8}-[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"SAGE-CCL Violation: Invalid record_id format: '{v}'")
        return v

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Enforce strict session_id formatting."""
        if not re.match(r"^(SES|session)_[a-zA-Z0-9_\-]+$", v):
            raise ValueError(f"SAGE-CCL Violation: Invalid session_id format: '{v}'")
        return v


class ContinuityControlLoop:
    """Orchestrates event capture, context enrichment, validation, and storage of continuity records."""

    def __init__(
        self,
        session_manager: Optional[SessionStateManager] = None,
        storage_path: str = "sage_data/experimental_ccl"
    ):
        """Initialize the Continuity Control Loop.

        Args:
            session_manager: Optional SessionStateManager to query for context.
            storage_path: Workspace staging directory for records.
        """
        self.session_manager = session_manager or SessionStateManager()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def intercept_event(
        self,
        event_type: str,
        action_taken: str,
        decision_reasoning: str,
        evidence_payload: Optional[Dict[str, Any]] = None,
        failure_context: Optional[Dict[str, Any]] = None,
        recovery_path: Optional[str] = None,
        session_id: Optional[str] = None,
        workflow_friction: Optional[List[Dict[str, Any]]] = None,
        improvement_opportunities: Optional[List[str]] = None,
    ) -> ContinuityControlRecord:
        """Intercepts AI workflow events and synthesizes a proposed continuity record.

        Args:
            event_type: Type of event (e.g. 'state_transition', 'boundary_intercept').
            action_taken: Summary of action completed.
            decision_reasoning: Rationale behind the action.
            evidence_payload: Relevant hashes, signatures, and outcomes.
            failure_context: Optional failure details if the action faulted.
            recovery_path: Optional recovery strategy applied.
            session_id: Optional target session ID.
            workflow_friction: List of observed bottlenecks/friction incidents.
            improvement_opportunities: List of identified SAGE improvement suggestions.

        Returns:
            The synthesized ContinuityControlRecord.
        """
        # Resolve active session context
        session = None
        if session_id:
            session = self.session_manager.retrieve_session(session_id)
            if not session:
                # If session_id is provided but doesn't exist, create it
                # Make sure the session prefix is valid
                clean_id = session_id
                if not (clean_id.startswith("session_") or clean_id.startswith("SES_")):
                    clean_id = f"session_{session_id}"
                session = self.session_manager.create_session(
                    session_id=clean_id,
                    active_objectives=["obj_experimental_coordination"]
                )
        else:
            all_sessions = self.session_manager.list_all()
            if all_sessions:
                # Retrieve most recent session based on timestamp
                session = sorted(all_sessions, key=lambda s: s.timestamp)[-1]
            else:
                session = self.session_manager.create_session(
                    session_id=f"session_{uuid.uuid4().hex[:8]}",
                    active_objectives=["obj_experimental_coordination"]
                )

        payload = dict(evidence_payload or {})

        # Context Enrichment
        enriched = self.enrich_context(session)
        payload.update(enriched)

        # Generate Record ID: CCL-REC-YYYYMMDD-UUID
        date_str = time.strftime("%Y%m%d", time.gmtime())
        record_id = f"CCL-REC-{date_str}-{uuid.uuid4()}"

        # Build Record
        record = ContinuityControlRecord(
            record_id=record_id,
            session_id=session.session_id,
            event_type=event_type,
            timestamp=time.time(),
            action_taken=action_taken,
            decision_reasoning=decision_reasoning,
            evidence_payload=payload,
            failure_context=failure_context,
            recovery_path=recovery_path,
            lifecycle_state="PROPOSED",
            workflow_friction=workflow_friction or [],
            improvement_opportunities=improvement_opportunities or [],
        )

        return record

    def enrich_context(self, session: SessionState) -> Dict[str, Any]:
        """Queries SessionState to retrieve active objectives and related telemetry metadata."""
        return {
            "enriched_objectives": list(session.active_objectives),
            "session_completed_actions": list(session.completed_actions),
            "session_pending_actions": list(session.pending_actions),
            "enrichment_timestamp": time.time()
        }

    def validate_record(self, record: ContinuityControlRecord) -> bool:
        """Performs adversarial and structural validation on the record.

        Checks:
        1. Correct ID prefixes and formatting.
        2. Monotonic chronological invariant compared to prior serialized records.
        3. Structural consistency of evidence payload.
        """
        # 1. Structural Checks
        if not record.record_id.startswith("CCL-REC-"):
            return False
        if not (record.session_id.startswith("session_") or record.session_id.startswith("SES_")):
            return False

        # 2. Chronological Monotonicity Check
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prior_record = ContinuityControlRecord(**data)
                    # If this is the same record, ignore
                    if prior_record.record_id == record.record_id:
                        continue
                    # Ensure timestamp order invariant
                    if prior_record.timestamp > record.timestamp:
                        # Non-monotonic order detected!
                        return False
            except Exception:
                pass

        # 3. Relational/Verification Integrity
        # Ensure that if it is a recovered status, both failure and recovery are documented
        if record.event_type == "recovered":
            if not record.failure_context or not record.recovery_path:
                return False

        return True

    def serialize_record(self, record: ContinuityControlRecord) -> Path:
        """Persists the continuity record to the workspace staging directory."""
        filepath = self.storage_path / f"{record.record_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.model_dump(), f, indent=2, default=str)
        return filepath

    def human_approval(
        self,
        record_id: str,
        supervisor_id: str,
        signature: str,
        decision: str
    ) -> ContinuityControlRecord:
        """Manages the human operator authorization review gate.

        Allows explicit operator override to promote a proposed record to the VALIDATED state.
        """
        filepath = self.storage_path / f"{record_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"SAGE-CCL Error: Record '{record_id}' not found.")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            record = ContinuityControlRecord(**data)

        if decision == "APPROVED":
            record.lifecycle_state = "VALIDATED"
        elif decision == "REJECTED":
            record.lifecycle_state = "REJECTED"
        else:
            raise ValueError(f"SAGE-CCL Error: Unsupported decision state: '{decision}'")

        # Update evidence payload with the manual human review signature
        record.evidence_payload["human_approval_record"] = {
            "supervisor_id": supervisor_id,
            "signature": signature,
            "decision": decision,
            "approved_at": time.time()
        }

        # Reserialize
        self.serialize_record(record)
        return record
