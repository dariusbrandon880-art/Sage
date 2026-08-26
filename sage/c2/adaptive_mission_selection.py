"""Adaptive Mission Selection Engine for SAGE C2 governance and candidate synthesis."""

from __future__ import annotations

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
    is_authorized: bool = False
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    decision_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "candidate_id": self.candidate_id,
            "frontier_id": self.frontier_id,
            "target_namespace": self.target_namespace,
            "priority_score": self.priority_score,
            "is_authorized": self.is_authorized,
            "rejection_reason": self.rejection_reason,
            "dependencies": sorted(self.dependencies),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class AdaptiveMissionSelectionEngine:
    """Synthesizes candidate proposals, failure intelligence, and dependency analysis."""

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
        deps = dependencies or []
        failures = failure_history or []
        is_protected = any(target_namespace.startswith(ns) for ns in PROTECTED_NAMESPACES)
        rejection_reason: Optional[str] = None
        is_authorized = False

        if is_protected and auth_token != self.system_token:
            rejection_reason = f"Target namespace '{target_namespace}' is protected and authorization token is missing/invalid."
            priority_score = 0.0
        else:
            failure_penalty = sum(
                0.25 for item in failures
                if item.get("target_namespace") == target_namespace or item.get("frontier_id") == frontier_id
            )
            priority_score = max(0.0, min(1.0, 1.0 - failure_penalty))
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
            risk_assessment={"is_protected_namespace": is_protected, "failure_count": len(failures), "evaluated_at": time.time()},
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
        evaluated = [
            self.evaluate_candidate(
                candidate_id=prop["candidate_id"],
                frontier_id=prop["frontier_id"],
                target_namespace=prop["target_namespace"],
                dependencies=prop.get("dependencies"),
                failure_history=failure_history,
                auth_token=auth_token,
            )
            for prop in proposals
        ]
        evaluated.sort(key=lambda packet: (packet.is_authorized, packet.priority_score), reverse=True)
        return evaluated
