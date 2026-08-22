"""Deterministic selection of consequential capability frontiers."""

from typing import List, Tuple
from sage.capability_registry import SAGECapability


_STATUS_SCORE = {
    "READY_FRONTIER": 5,
    "PARTIAL": 4,
    "BLOCKED": 3,
    "RESEARCH_ONLY": 2,
    "ACTIVE": 1,
    "DEPRECATED": 0,
}


def rank_frontiers(capabilities: List[SAGECapability], limit: int = 5) -> List[Tuple[str, int]]:
    """Rank non-validated work without promoting it to canonical status."""
    candidates = [
        cap for cap in capabilities
        if cap.lifecycle_status in {"READY_FRONTIER", "PARTIAL", "BLOCKED", "RESEARCH_ONLY"}
        or cap.validation_status != "VALIDATED"
    ]

    scored = []
    for cap in candidates:
        score = _STATUS_SCORE.get(cap.lifecycle_status, 0)
        score += min(len(cap.dependencies), 3)
        if cap.incompletion_reason:
            score += 1
        scored.append((cap.capability_id, score))

    return sorted(scored, key=lambda item: (-item[1], item[0]))[:limit]
