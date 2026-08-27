"""Adaptive Mission Selection Engine."""

from __future__ import annotations

import time
from typing import List, Optional
from pydantic import BaseModel, Field
from sage.c2.reconvergence_synthesizer import ReconvergenceEvidencePackage


class CandidateDecisionPacket(BaseModel):
    candidate_id: str
    target: str
    rank_score: float
    is_authorized: bool = False
    reasons: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class AdaptiveMissionSelectionEngine:
    def __init__(self):
        self.decision_history: List[CandidateDecisionPacket] = []

    def rank_candidate(self, candidate_id: str, target: str, base_priority: float,
                       prior_wave_package: Optional[ReconvergenceEvidencePackage] = None) -> CandidateDecisionPacket:
        score = base_priority
        reasons = [f"Base priority: {base_priority}"]
        if prior_wave_package:
            completion_rate = prior_wave_package.first_pass_verification_rate
            score += completion_rate * 0.1
            reasons.append(f"Adjusted by prior wave completion rate ({completion_rate}%): +{completion_rate * 0.1:.2f}")
        packet = CandidateDecisionPacket(candidate_id=candidate_id, target=target,
                                         rank_score=round(score, 2), is_authorized=False, reasons=reasons)
        self.decision_history.append(packet)
        return packet
