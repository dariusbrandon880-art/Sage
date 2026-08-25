"""Adaptive Mission Selection Engine for SAGE C2.

Synthesizes failure intelligence, capability lineage, mission intake, and dependency boundaries
into ranked decision packets (CandidateDecisionPacket).
Enforces default unapproved posture (is_authorized=False) and falsification checks
against protected core namespaces.
"""

import time
import hashlib
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class CandidateDecisionPacket(BaseModel):
    """Represents a ranked candidate proposal packet evaluated by the C2 decision engine."""
    candidate_id: str = Field(..., description="Unique candidate proposal ID")
    title: str = Field(..., description="Short descriptive title of the proposal")
    target_namespace: str = Field(..., description="Primary code/doc namespace affected")
    risk_score: float = Field(..., description="Calculated risk score (0.0 = low, 1.0 = high)")
    priority_score: float = Field(..., description="Ranked priority score (0.0 = low, 10.0 = max)")
    is_protected_namespace: bool = Field(False, description="True if proposal touches protected core namespaces")
    is_authorized: bool = Field(False, description="Fail-closed authorization status (default False)")
    rejection_reasons: List[str] = Field(default_factory=list, description="List of blocking policy violations")
    evidence_requirements: List[str] = Field(default_factory=list, description="Required evidence receipts")
    packet_hash: str = Field("", description="Cryptographic SHA-256 digest of packet payload")


class AdaptiveMissionSelectionEngine:
    """Evaluates and ranks discovery proposals for C2 governance decision-making."""

    PROTECTED_NAMESPACES = [
        "sage/core/",
        "sage/runtime/",
        "sage/acr/",
        "sage/agents/",
        "docs/governance/",
        ".github/workflows/"
    ]

    def is_protected(self, path: str) -> bool:
        """Check if a target path lies inside a protected core namespace."""
        return any(path.startswith(p) or p in path for p in self.PROTECTED_NAMESPACES)

    def evaluate_candidate(
        self,
        candidate_id: str,
        title: str,
        target_namespace: str,
        impact_score: float = 5.0,
        historical_failures: Optional[List[str]] = None
    ) -> CandidateDecisionPacket:
        """Evaluate a candidate proposal and return a structured, ranked decision packet."""
        rejections: List[str] = []
        is_protected = self.is_protected(target_namespace)

        # Fail-closed check for protected namespaces
        if is_protected:
            rejections.append(f"Target namespace '{target_namespace}' violates core protected boundary.")

        # Fail-closed check for past failure matches
        if historical_failures:
            rejections.append(f"Candidate matches {len(historical_failures)} known failure patterns.")

        # Calculate risk and priority scores
        base_risk = 0.8 if is_protected else 0.2
        if historical_failures:
            base_risk += 0.3
        risk_score = min(1.0, base_risk)

        priority_score = round(impact_score * (1.0 - risk_score), 2)

        # Cryptographic hash computation
        payload_str = f"{candidate_id}:{target_namespace}:{risk_score}:{priority_score}"
        pkt_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        return CandidateDecisionPacket(
            candidate_id=candidate_id,
            title=title,
            target_namespace=target_namespace,
            risk_score=risk_score,
            priority_score=priority_score,
            is_protected_namespace=is_protected,
            is_authorized=False,  # Enforce fail-closed authorization posture
            rejection_reasons=rejections,
            evidence_requirements=[
                "evidence_capture/ccl_operational_feedback.json",
                f"evidence_capture/{candidate_id}_evidence.json"
            ],
            packet_hash=pkt_hash
        )

    def rank_candidates(self, candidates: List[CandidateDecisionPacket]) -> List[CandidateDecisionPacket]:
        """Rank candidates by priority score descending while filtering protected/rejected proposals."""
        valid_candidates = [c for c in candidates if not c.is_protected_namespace and not c.rejection_reasons]
        return sorted(valid_candidates, key=lambda x: x.priority_score, reverse=True)
