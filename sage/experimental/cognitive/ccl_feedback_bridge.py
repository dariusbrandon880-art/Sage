"""Closed-Loop CCL Outcome Feedback Bridge."""

from __future__ import annotations
import hashlib
import time
from typing import List
from pydantic import BaseModel, Field
from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus


class FeedbackBridgeReceipt(BaseModel):
    receipt_id: str
    reconciliation_digest: str
    candidate_id: str
    adjusted_score: float
    feedback_applied: bool
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""
    def compute_hash(self) -> str:
        payload = f"{self.receipt_id}:{self.reconciliation_digest}:{self.candidate_id}:{self.adjusted_score}:{self.feedback_applied}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CCLOutcomeFeedbackBridge:
    def __init__(self, mission_selection_engine: AdaptiveMissionSelectionEngine):
        self.selection_engine = mission_selection_engine
        self.receipts: List[FeedbackBridgeReceipt] = []

    def apply_outcome_feedback(self, reconciliation: OutcomeReconciliation, candidate_id: str,
                                target: str, base_priority: float) -> tuple[CandidateDecisionPacket, FeedbackBridgeReceipt]:
        packet = self.selection_engine.rank_candidate(candidate_id=candidate_id, target=target, base_priority=base_priority)
        multiplier = 1.2 if reconciliation.status == OutcomeReconciliationStatus.RECONCILED else 0.5
        adjusted_score = round(packet.rank_score * multiplier, 2)
        packet.rank_score = adjusted_score
        packet.reasons.append(f"CCL outcome feedback multiplier applied ({multiplier}x): score adjusted to {adjusted_score}")
        rcpt = FeedbackBridgeReceipt(receipt_id=f"ccl_fb_rcpt_{int(time.time() * 1000)}",
                                     reconciliation_digest=reconciliation.reconciliation_digest,
                                     candidate_id=candidate_id, adjusted_score=adjusted_score, feedback_applied=True)
        rcpt.receipt_hash = rcpt.compute_hash(); self.receipts.append(rcpt)
        return packet, rcpt
