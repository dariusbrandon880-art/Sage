"""Pydantic models for the SAGE Policy Enforcement Kernel (SPEK) v1.1."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleState(str, Enum):
    """SAGE SPEK lifecycle states."""
    PROPOSED = "PROPOSED"
    EVALUATED = "EVALUATED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class Proposal(BaseModel):
    """Schema representing a rule or architectural decision proposed to SAGE SPEK."""

    proposal_id: str
    description: str
    category: str
    author: str
    signature: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    state: RuleState = RuleState.PROPOSED


class HypothesisNode(BaseModel):
    """HDG v2 Epistemic Causality Node representation."""

    node_id: str
    description: str
    parent_ids: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    validation_score: float = 0.0
    contradictions: List[str] = Field(default_factory=list)  # List of contradictory node IDs
    is_promoted: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpekReceipt(BaseModel):
    """Schema for a signed, append-only cryptographic receipt for SPEK audits."""

    receipt_id: str
    proposal_id: str
    timestamp: str
    lifecycle_state: str
    execution_permission: bool
    authority_integrity_score: float
    hdg_trace: List[Dict[str, Any]] = Field(default_factory=list)
    attestation_signature: str
    receipt_hash: str
    previous_receipt_hash: str
