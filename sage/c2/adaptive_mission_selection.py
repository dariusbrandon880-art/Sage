"""Adaptive Mission Selection Engine for SAGE C2 governance and candidate decision synthesis."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


PROTECTED_NAMESPACES = [
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
]


class CandidateDecisionPacket(BaseModel):
    """Immutable decision packet for candidate mission proposals."""

    candidate_id: str
    frontier_id: str
    target_namespace: str
    priority_score: float
    is_authorized: bool = False
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    decision_hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint for the decision packet."""
        payload = {
            "candidate_id": self.candidate_id,
            "frontier_id": self.frontier_id,
            "target_namespace": self.target_namespace,
            "priority_score": self.priority_score,
            "is_authorized": self.is_authorized,
            "rejection_reason": self.rejection_reason,
            "dependencies": sorted(self.dependencies),
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class AdaptiveMissionSelectionEngine:
    """Synthesizes candidate proposals, failure intelligence, and dependency analysis into decision packets."""

    def __init__(self, system_token: str = "SAGE_SYSTEM_AUTH_TOKEN"):
        self.system_token = system_token

    def evaluate_candidate(
        self,
        candidate_id: str,
        frontier_id: str,
        target_namespace: str,
        dependencies: Optional[List[str]] = None,
        failure_history: Optional[List[Dict[str, Any]]] = None,
        auth_token: Optional[str] = None,
    ) -> CandidateDecisionPacket:
        """Evaluate a single candidate mission proposal."""
        deps = dependencies or []
        failures = failure_history or []

        rejection_reason: Optional[str] = None
        is_authorized = False

        # Check protected namespace boundaries
        is_protected = any(target_namespace.startswith(ns) for ns in PROTECTED_NAMESPACES)
        if is_protected and auth_token != self.system_token:
            rejection_reason = f"Target namespace '{target_namespace}' is protected and authorization token is missing/invalid."
            priority_score = 0.0
        else:
            # Check failure intelligence overlap
            failure_penalty = 0.0
            for item in failures:
                if item.get("target_namespace") == target_namespace or item.get("frontier_id") == frontier_id:
                    failure_penalty += 0.25

            base_score = 1.0 - failure_penalty
            priority_score = max(0.0, min(1.0, base_score))

            if priority_score >= 0.5:
                is_authorized = True
            else:
                rejection_reason = f"Priority score {priority_score:.2f} fell below minimum authorization threshold 0.50 due to failure history."

        packet = CandidateDecisionPacket(
            candidate_id=candidate_id,
            frontier_id=frontier_id,
            target_namespace=target_namespace,
            priority_score=priority_score,
            is_authorized=is_authorized,
            risk_assessment={
                "is_protected_namespace": is_protected,
                "failure_count": len(failures),
                "evaluated_at": time.time(),
            },
            dependencies=deps,
            rejection_reason=rejection_reason,
        )
        packet.decision_hash = packet.compute_hash()
        return packet

    def rank_candidates(
        self,
        proposals: List[Dict[str, Any]],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        auth_token: Optional[str] = None,
    ) -> List[CandidateDecisionPacket]:
        """Rank and evaluate multiple candidate mission proposals."""
        evaluated = []
        for prop in proposals:
            packet = self.evaluate_candidate(
                candidate_id=prop["candidate_id"],
                frontier_id=prop["frontier_id"],
                target_namespace=prop["target_namespace"],
                dependencies=prop.get("dependencies"),
                failure_history=failure_history,
                auth_token=auth_token,
            )
            evaluated.append(packet)

        # Sort by priority_score descending, authorized first
        evaluated.sort(key=lambda p: (p.is_authorized, p.priority_score), reverse=True)
        return evaluated
