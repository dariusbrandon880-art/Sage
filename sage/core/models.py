"""Core models for SAGE Policy Enforcement Kernel (SPEK) v1.1."""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SPEKLifecycleState(str, Enum):
    """Enforces rule candidate and decision promotion states under SPEK v1.1."""

    PROPOSED = "PROPOSED"
    EVALUATED = "EVALUATED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class SPEKReceipt(BaseModel):
    """Immutable chained EAS-001 receipt record validating promotion or transition audits."""

    # Core Identifiers
    candidate_id: str
    title: str
    parent_ids: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    validation_score: float = 0.0

    # Chaining/Tracking/Timestamps
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: SPEKLifecycleState = SPEKLifecycleState.PROPOSED
    lifecycle_state: SPEKLifecycleState = SPEKLifecycleState.PROPOSED
    execution_permission: bool = True
    authority_integrity_score: float = 1.0
    hdg_trace: List[str] = Field(default_factory=list)

    # Security/Attestation (HMAC / Trace linkage)
    attestation_signature: str = ""
    receipt_hash: str = ""
    previous_receipt_hash: str = ""
    parent_receipt_hash: str = ""

    metadata: Dict[str, Any] = Field(default_factory=dict)
