"""Adaptive Mission Selection Engine for SAGE C2 governance and candidate decision synthesis."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

PROTECTED_NAMESPACES = ["sage/core/", "sage/runtime/", "sage/acr/", "sage/agents/"]

class CandidateDecisionPacket(BaseModel):
    """Immutable decision packet for candidate mission proposals."""
    candidate_id: str
    frontier_id: str
    target_namespace: str
    priority_score: float
    rank_score: float = 1.0
    reasons: List[str] = Field(default_factory=list)
    is_authorized: bool = False
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    decision_hash: str = ""

    def compute_hash(self) -> str:
        payload = {"candidate_id": self.candidate_id, "frontier_id": self.frontier_id, "target_namespace": self.target_namespace, "priority_score": self.priority_score, "is_authorized": self.is_authorized, "rejection_reason": self.rejection_reason, "dependencies": sorted(self.dependencies)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

class AdaptiveMissionSelectionEngine:
    """Synthesizes candidate proposals, failure intelligence, and dependencies into decision packets."""
    def __init__(self, system_token: str = "SAGE_SYSTEM_AUTH_TOKEN"):
        self.system_token = system_token

    def evaluate_candidate(self, candidate_id: str, frontier_id: str, target_namespace: str, dependencies: Optional[List[str]] = None, failure_history: Optional[List[Dict[str, Any]]] = None, auth_token: Optional[str] = None) -> CandidateDecisionPacket:
        failures = failure_history or []
        is_protected = any(target_namespace.startswith(ns) for ns in PROTECTED_NAMESPACES)
        rejection_reason = None
        is_authorized = False
        if is_protected and auth_token != self.system_token:
            rejection_reason = f"Target namespace '{target_namespace}' is protected and authorization token is missing/invalid."
            priority_score = 0.0
        else:
            failure_penalty = sum(0.25 for item in failures if item.get("target_namespace") == target_namespace or item.get("frontier_id") == frontier_id)
            priority_score = max(0.0, min(1.0, 1.0 - failure_penalty))
            if priority_score >= 0.5:
                is_authorized = True
            else:
                rejection_reason = f"Priority score {priority_score:.2f} fell below minimum authorization threshold 0.50 due to failure history."
        packet = CandidateDecisionPacket(candidate_id=candidate_id, frontier_id=frontier_id, target_namespace=target_namespace, priority_score=priority_score, is_authorized=is_authorized, risk_assessment={"is_protected_namespace": is_protected, "failure_count": len(failures), "evaluated_at": time.time()}, dependencies=dependencies or [], rejection_reason=rejection_reason)
        packet.decision_hash = packet.compute_hash()
        return packet

    def rank_candidates(self, proposals: List[Dict[str, Any]], failure_history: Optional[List[Dict[str, Any]]] = None, auth_token: Optional[str] = None) -> List[CandidateDecisionPacket]:
        evaluated = [self.evaluate_candidate(prop["candidate_id"], prop["frontier_id"], prop["target_namespace"], prop.get("dependencies"), failure_history, auth_token) for prop in proposals]
        evaluated.sort(key=lambda p: (p.is_authorized, p.priority_score), reverse=True)
        return evaluated

    def rank_candidate(self, candidate_id: str, target: str, base_priority: float = 1.0) -> CandidateDecisionPacket:
        """Evaluates single candidate proposal for closed-loop feedback ranking."""
        packet = self.evaluate_candidate(
            candidate_id=candidate_id,
            frontier_id=f"FRONTIER-{candidate_id}",
            target_namespace=target,
        )
        packet.rank_score = round(base_priority, 2)
        packet.reasons.append(f"Initial ranking evaluated for candidate '{candidate_id}'")
        return packet
