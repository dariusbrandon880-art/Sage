"""SAGE Learning Runtime - Continuity Intake."""

import uuid
from typing import Any, Dict
from sage.learning.knowledge_candidate import KnowledgeCandidate


class LearningIntake:
    """Intakes raw events or facts and normalizes them for memory processing and pattern extraction."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    def ingest_fact(self, source: str, data: Dict[str, Any], confidence_score: float = 0.5) -> KnowledgeCandidate:
        """Normalized fact intake to generate a raw knowledge candidate."""
        candidate_id = data.get("candidate_id") or f"cand_{uuid.uuid4().hex[:8]}"

        candidate = KnowledgeCandidate(
            candidate_id=candidate_id,
            source_reference=source,
            knowledge_type=data.get("type", "general_learning"),
            confidence_score=confidence_score,
            evidence_links=data.get("evidence", []),
            validation_state="PROPOSED",
            promotion_status="PENDING",
            content=data,
        )
        return candidate
