"""SAGE Learning Runtime - Knowledge Candidate Model."""

from typing import Any, List
from pydantic import BaseModel, Field


class KnowledgeCandidate(BaseModel):
    """Represents a potential learned item within the SAGE Learning Runtime Layer."""

    candidate_id: str
    source_reference: str
    knowledge_type: str  # e.g., "design_pattern", "architectural_rule", "general_learning"
    confidence_score: float = 0.0
    evidence_links: List[str] = Field(default_factory=list)
    validation_state: str = "PROPOSED"  # PROPOSED, EVALUATED, VALIDATED, APPROVED, REJECTED
    promotion_status: str = "PENDING"   # PENDING, QUEUED, PROMOTED, ABORTED
    content: dict[str, Any] = Field(default_factory=dict)
