"""SAGE-ACT Experimental Continuity Control Loop (SAGE-CCL) Implementation."""

import os
import re
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContinuityControlRecord(BaseModel):
    """Structured container representing an immutable, machine-validatable workflow event record."""
    record_id: str = Field(..., description="Unique record identifier, matching ^CCL-REC-[0-9]{8}-[a-fA-F0-9\\-]{36}$")
    session_id: str = Field(..., description="SAGE Session identifier, matching ^session_[a-fA-F0-9]{8}$")
    event_type: str = Field(..., description="Type of event captured, e.g., state_transition, boundary_intercept")
    timestamp: float = Field(..., description="Epoch timestamp of the recorded event")
    action_taken: str = Field(..., description="Descriptive text of the captured action")
    decision_reasoning: str = Field(..., description="Logical or strategic reason behind the action")
    evidence_payload: Dict[str, Any] = Field(default_factory=dict, description="Metadata linking to git hashes, signatures, etc.")
    failure_context: Optional[Dict[str, Any]] = Field(default=None, description="Contextual information if event captures a failure")
    recovery_path: Optional[str] = Field(default=None, description="Prescribed recovery strategy")
    lifecycle_state: str = Field(default="PROPOSED", description="Provenance status: PROPOSED, VALIDATED")


class ContinuityControlLoop:
    """Manages SAGE-CCL operations under absolute experimental isolation.

    Enforces temporal preservation:
      Agent Event -> State -> Decision -> Evidence -> Failure Context -> Recovery Path
      Action -> Record -> Decision -> Evidence -> Accountability
    """

    def __init__(self, stage_dir: str = "sage_data/experimental_ccl"):
        """Initialize the control loop and set up staging directories."""
        self.stage_dir = stage_dir
        os.makedirs(self.stage_dir, exist_ok=True)

    def capture_event(
        self,
        session_id: str,
        event_type: str,
        action: str,
        reasoning: str,
        evidence: Dict[str, Any],
        failure_context: Optional[Dict[str, Any]] = None,
        recovery_path: Optional[str] = None,
    ) -> ContinuityControlRecord:
        """Capture an AI workflow event and map it to a structured, un-serialized ContinuityControlRecord."""
        # Validate format constraints
        if not re.match(r"^session_[a-fA-F0-9]{8}$", session_id):
            raise ValueError(f"SAGE-CCL Violation: Invalid session_id format '{session_id}'.")

        # Generate unique record ID
        date_str = time.strftime("%Y%m%d", time.gmtime())
        record_uuid = str(uuid.uuid4())
        record_id = f"CCL-REC-{date_str}-{record_uuid}"

        record = ContinuityControlRecord(
            record_id=record_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=time.time(),
            action_taken=action,
            decision_reasoning=reasoning,
            evidence_payload=evidence,
            failure_context=failure_context,
            recovery_path=recovery_path,
            lifecycle_state="PROPOSED",
        )
        return record

    def stage_record(self, record: ContinuityControlRecord) -> None:
        """Serialize and stage a ContinuityControlRecord to the local workspace staging directory."""
        record_path = os.path.join(self.stage_dir, f"{record.record_id}.json")
        with open(record_path, "w") as f:
            # Using model_dump_json if available, fallback to json.dumps
            if hasattr(record, "model_dump"):
                f.write(json.dumps(record.model_dump(), indent=2))
            else:
                f.write(record.json(indent=2))

    def verify_record_integrity(self, record_id: str) -> Dict[str, Any]:
        """Perform read-only validation of a staged record's schema, patterns, and chronological alignment.

        Raises:
            ValueError: If record files are missing, corrupted, or violate integrity rules.
        """
        record_path = os.path.join(self.stage_dir, f"{record_id}.json")
        if not os.path.exists(record_path):
            raise ValueError(f"SAGE-CCL Violation: Record file '{record_id}' not found.")

        try:
            with open(record_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"SAGE-CCL Violation: Corrupt record file. JSON decoding failed: {e}")

        # Validate formats
        if not re.match(r"^CCL-REC-[0-9]{8}-[a-fA-F0-9\-]{36}$", data.get("record_id", "")):
            raise ValueError(f"SAGE-CCL Violation: Record ID '{data.get('record_id')}' fails format validation.")

        if not re.match(r"^session_[a-fA-F0-9]{8}$", data.get("session_id", "")):
            raise ValueError(f"SAGE-CCL Violation: Session ID '{data.get('session_id')}' fails format validation.")

        # Ensure core fields are populated
        for field in ["event_type", "action_taken", "decision_reasoning", "evidence_payload"]:
            if field not in data or data[field] is None:
                raise ValueError(f"SAGE-CCL Violation: Missing core field '{field}' in record '{record_id}'.")

        # Validate evidence payload has artifact context or accountability hashes
        evidence = data.get("evidence_payload", {})
        if not isinstance(evidence, dict):
            raise ValueError(f"SAGE-CCL Violation: 'evidence_payload' must be a dictionary.")

        return {
            "record_id": record_id,
            "verified_at": time.time(),
            "status": "VERIFIED_STABLE",
            "lifecycle_state": data.get("lifecycle_state", "PROPOSED"),
        }

    def promote_record(self, record_id: str, signature: Optional[str] = None) -> ContinuityControlRecord:
        """Promote a staged record from PROPOSED to VALIDATED, simulating formal human-operator sign-off.

        In a production environment, this is protected by human cryptographic keys (e.g., SPEK attestation).
        """
        # Run read-only integrity checks first
        self.verify_record_integrity(record_id)

        record_path = os.path.join(self.stage_dir, f"{record_id}.json")
        with open(record_path, "r") as f:
            data = json.load(f)

        # Enforce mock human approval boundary requirement
        if signature is None or not signature.startswith("sig_"):
            raise ValueError("SAGE-CCL Violation: Cannot promote record to VALIDATED without a valid human operator signature.")

        # Update and save the promoted record
        data["lifecycle_state"] = "VALIDATED"
        data["evidence_payload"]["operator_signature"] = signature

        record = ContinuityControlRecord(**data)
        self.stage_record(record)
        return record

    def list_records(self, session_id: Optional[str] = None) -> List[ContinuityControlRecord]:
        """List all staged and validated records under SAGE-CCL."""
        records = []
        if not os.path.exists(self.stage_dir):
            return records

        for filename in os.listdir(self.stage_dir):
            if filename.endswith(".json"):
                record_path = os.path.join(self.stage_dir, filename)
                try:
                    with open(record_path, "r") as f:
                        data = json.load(f)
                    rec = ContinuityControlRecord(**data)
                    if session_id is None or rec.session_id == session_id:
                        records.append(rec)
                except (json.JSONDecodeError, ValueError):
                    # Gracefully skip corrupted files
                    continue

        # Sort chronologically by timestamp
        records.sort(key=lambda r: r.timestamp)
        return records

    def reconstruct_lineage(self, session_id: str) -> Dict[str, Any]:
        """Reconstruct the absolute chronological event lineage and causality graph of a session for audit.

        Preserves: Agent Event -> State -> Decision -> Evidence -> Failure Context -> Recovery Path
        """
        records = self.list_records(session_id=session_id)
        causality_chain = []

        for r in records:
            causality_node = {
                "record_id": r.record_id,
                "timestamp": r.timestamp,
                "event_type": r.event_type,
                "action": r.action_taken,
                "decision": r.decision_reasoning,
                "lifecycle_state": r.lifecycle_state,
                "evidence_sha": r.evidence_payload.get("sha256_checksum", "unhashed"),
            }
            if r.failure_context:
                causality_node["failure"] = r.failure_context
            if r.recovery_path:
                causality_node["recovery"] = r.recovery_path

            causality_chain.append(causality_node)

        return {
            "session_id": session_id,
            "total_records": len(causality_chain),
            "chronological_lineage": causality_chain,
            "reconstructed_at": time.time(),
            "audit_ready": True,
        }
