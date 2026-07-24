"""SAGE Learning Runtime - Validation Router connecting Learning outputs to SPEK."""

from typing import Any, Tuple
from sage.learning.knowledge_candidate import KnowledgeCandidate


class ValidationRouter:
    """Routes candidates through the strict validation system / SPEK governance gate."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    def route_to_validation(self, candidate: KnowledgeCandidate) -> Tuple[bool, str]:
        """Submit a learned candidate through SAGE validation governance.

        If approved, promotes the item. If rejected, isolates it in negative logs.
        """
        from sage.models import MemoryObject, ConfidenceLevel

        memory_id = f"mem_learning_{candidate.candidate_id}"

        tags = ["learning", candidate.knowledge_type]
        if candidate.knowledge_type in ("architectural_rule", "rule_candidate", "rule"):
            tags.append("rule_candidate")

        content_data = candidate.content.copy() if candidate.content else {}
        content_data["candidate_id"] = candidate.candidate_id

        # We DO NOT auto-sign here. The candidate must present its own authorized signature
        # to pass SAGE-RT-KL-002 and SPEK governance gates.

        m_obj = MemoryObject(
            id=memory_id,
            object_type=candidate.knowledge_type,
            content=content_data,
            tags=tags,
            confidence=ConfidenceLevel.HYPOTHESIS,
        )

        self.runtime.memory.store(m_obj)

        is_valid, failed_rules = self.runtime.validation.validate_memory(memory_id)

        if is_valid:
            if candidate.confidence_score >= 0.8:
                candidate.validation_state = "APPROVED"
                candidate.promotion_status = "QUEUED"
                success, result = self.runtime.validation.promote_to_archive(
                    memory_id,
                    title=f"Learned Knowledge: {candidate.candidate_id}",
                    tags=tags,
                )
                if success:
                    candidate.promotion_status = "PROMOTED"
                    return True, f"Knowledge successfully validated and promoted: {result}"
                else:
                    candidate.promotion_status = "ABORTED"
                    return False, f"Failed to promote valid candidate to archive: {result}"
            else:
                candidate.validation_state = "REJECTED"
                candidate.promotion_status = "ABORTED"
                return False, "Rejected: Confidence score below evidence threshold (0.8)."
        else:
            candidate.validation_state = "REJECTED"
            candidate.promotion_status = "ABORTED"
            return False, f"Rejected: SAGE SPEK Validation failed: {', '.join(failed_rules)}"
