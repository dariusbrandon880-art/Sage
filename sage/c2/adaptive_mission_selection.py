"""Adaptive Mission Selection Engine.

Synthesizes candidate proposals from failure intelligence, capability lineage,
mission intake, and 20-cell wave completion rates into ranked CandidateDecisionPackets.
Enforces default unapproved posture (`is_authorized=False`).
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.c2.reconvergence_synthesizer import ReconvergenceEvidencePackage


class CandidateDecisionPacket(BaseModel):
    """Ranked mission candidate decision packet."""
    candidate_id: str
    target: str
    rank_score: float
    is_authorized: bool = False
    reasons: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class AdaptiveMissionSelectionEngine:
    """Engine selecting and ranking mission candidates based on operational feedback."""

    def __init__(self):
        self.decision_history: List[CandidateDecisionPacket] = []

    def rank_candidate(
        self,
        candidate_id: str,
        target: str,
        base_priority: float,
        prior_wave_package: Optional[ReconvergenceEvidencePackage] = None,
    ) -> CandidateDecisionPacket:
        """Ranks candidate mission considering prior wave 20-cell completion rates."""
        score = base_priority
        reasons = [f"Base priority: {base_priority}"]

        if prior_wave_package:
            completion_rate = prior_wave_package.first_pass_verification_rate
            score += completion_rate * 0.1
            reasons.append(f"Adjusted by prior wave completion rate ({completion_rate}%): +{completion_rate * 0.1:.2f}")

        packet = CandidateDecisionPacket(
            candidate_id=candidate_id,
            target=target,
            rank_score=round(score, 2),
            is_authorized=False,  # Fails closed / unauthorized by default
            reasons=reasons,
        )
        self.decision_history.append(packet)
        return packet
