"""SAGE Memory Importance and Pruning Pipeline (Track C.11).

Calibrates the lifecycle relevance of memory objects using temporal half-life decay.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from sage.models import MemoryObject


class MemoryImportancePipeline:
    """Evaluates memory significance, assigns importance indexes, and prunes low-relevance logs."""

    def __init__(self, memory_store, half_life_days: float = 7.0):
        self.memory = memory_store
        self.half_life_days = half_life_days

    def evaluate_object_importance(self, obj: MemoryObject) -> float:
        """Calculates memory object lifecycle relevance index (0.0 to 1.0).

        Considers tag density, usage patterns, and exponential decay over time.
        """
        # Base importance derived from tag richness and content size
        base = 0.5
        if obj.tags:
            base += min(0.3, len(obj.tags) * 0.1)

        content_size = len(str(obj.content))
        if content_size > 200:
            base += 0.1

        # Exponential decay factor
        age_delta = datetime.now(timezone.utc) - obj.created_at
        age_days = age_delta.total_seconds() / 86400.0

        decay_factor = 0.5 ** (age_days / self.half_life_days)
        importance_score = min(1.0, max(0.01, round(base * decay_factor, 4)))

        return importance_score

    def run_importance_audit(self, prunable_threshold: float = 0.15) -> Dict[str, Any]:
        """Audits all memory objects, flagging prunable candidates.

        Returns:
            Dict containing count analyzed, candidates for archiving, and pruned counts.
        """
        objects = self.memory.list_all()
        audited = {}
        prune_candidates = []

        for obj in objects:
            score = self.evaluate_object_importance(obj)
            audited[obj.id] = score
            if score < prunable_threshold:
                prune_candidates.append(obj.id)

        return {
            "total_analyzed": len(objects),
            "scores": audited,
            "prune_candidates": prune_candidates,
            "prune_candidates_count": len(prune_candidates),
        }
