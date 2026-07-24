"""SAGE SPEK Core Models - Zero Dependency Dataclasses."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Proposal:
    """Represents a rule, decision, or control specification proposal."""

    proposal_id: str
    title: str
    content: Dict[str, Any]
    evidence_references: List[str] = field(default_factory=list)
    lifecycle_state: str = "PROPOSED"  # PROPOSED, EVALUATED, VALIDATED, APPROVED, REJECTED, ARCHIVED
    signature: Optional[str] = None


@dataclass
class HypothesisNode:
    """Represents a node in the HDG v2 Epistemic Causality Engine."""

    node_id: str
    parent_ids: List[str] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    validation_score: float = 0.0
    contradiction_markers: List[str] = field(default_factory=list)
    promotion_eligible: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EASReceipt:
    """Represents an immutable chained EAS-001 audit receipt record."""

    receipt_id: str
    timestamp: str
    lifecycle_state: str
    execution_permission: bool
    authority_integrity_score: float
    hdg_trace: List[str]
    cryptographic_attestation: str
    receipt_hash: str
    previous_receipt_hash: str
