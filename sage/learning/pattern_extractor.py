"""SAGE Learning Runtime - Pattern Extraction Pipeline."""

from typing import List
from sage.learning.knowledge_candidate import KnowledgeCandidate


class PatternExtractor:
    """Extracts repeatable design patterns or control structures from input streams."""

    def __init__(self, evidence_threshold: float = 0.8):
        self.evidence_threshold = evidence_threshold

    def extract_patterns(self, candidate: KnowledgeCandidate) -> List[KnowledgeCandidate]:
        """Inspects a candidate item and extracts refined repeatable patterns as candidates."""
        refined_candidates = []
        content = candidate.content or {}

        # Look for repeating attributes like "rules", "reusable", or recurring tasks
        if "reusable" in content or "pattern" in content or "rule" in content or candidate.confidence_score >= self.evidence_threshold:
            # Generate refined candidate with a unique ID to prevent overwrites
            refined = candidate.model_copy()
            refined.candidate_id = f"pattern_{candidate.candidate_id}"
            refined.knowledge_type = "design_pattern" if "pattern" in content else "architectural_rule"
            refined.confidence_score = min(candidate.confidence_score + 0.1, 1.0)
            refined_candidates.append(refined)

        return refined_candidates
