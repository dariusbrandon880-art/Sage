"""SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) Data Models."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ERIPActorIdentity(BaseModel):
    """Actor identity model for ERIP evidence packages."""

    agent_id: str
    name: str
    role: str
    governance_tier: str
    signature: str
    key_fingerprint: str


class ERIPParentReceipt(BaseModel):
    """Parent receipt reference model for ERIP ancestry reconciliation."""

    parent_task_id: str
    parent_passport_hash: str
    parent_signature: str


class ERIPCompliancePack(BaseModel):
    """Compliance pack representation for SAGE-ERIP intake."""

    pack_id: str = Field(default_factory=lambda: f"erip_pack_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    nonce: str = Field(default_factory=lambda: f"nonce_{uuid.uuid4().hex[:12]}")
    actor_identity: Dict[str, Any]
    cmaps_payload: Dict[str, Any]
    hash_chain: List[str] = Field(default_factory=list)
    terminal_root_hash: str = ""
    parent_receipt: Optional[Dict[str, Any]] = None
    historical_archive_ref: Optional[str] = None


class ERIPContradictionFinding(BaseModel):
    """Structured description of a detected evidence contradiction."""

    contradiction_type: str
    description: str
    affected_boundary: str


class ERIPValidationResult(BaseModel):
    """Deterministic validation result emitted by ERIP Validation Core."""

    validation_id: str = Field(default_factory=lambda: f"val_erip_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor_identity: Dict[str, Any]
    stages_executed: List[str] = Field(default_factory=list)
    status: str  # "PASS" or "REJECT"
    failed_stage: Optional[str] = None
    failure_reason: Optional[str] = None
    contradiction_findings: List[Dict[str, Any]] = Field(default_factory=list)
    integrity_root_verified: bool = False
    provenance_hash: str = ""
    promoted_to_canonical: bool = False  # Hard rule: Never promoted to CANONICAL automatically

    def compute_provenance_hash(self) -> str:
        """Compute deterministic cryptographic SHA-256 provenance hash for this result."""
        material = {
            "validation_id": self.validation_id,
            "timestamp": self.timestamp,
            "actor_identity": self.actor_identity,
            "stages_executed": self.stages_executed,
            "status": self.status,
            "failed_stage": self.failed_stage,
            "failure_reason": self.failure_reason,
            "contradiction_findings": self.contradiction_findings,
            "integrity_root_verified": self.integrity_root_verified,
            "promoted_to_canonical": self.promoted_to_canonical,
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary with populated provenance hash."""
        if not self.provenance_hash:
            self.provenance_hash = self.compute_provenance_hash()
        data = self.model_dump()
        data["provenance_hash"] = self.provenance_hash
        return data
