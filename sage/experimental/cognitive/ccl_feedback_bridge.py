"""SAGE Closed-Loop Capability Outcome Feedback Bridge.

Connects OutcomeReconciliation and SAGIEvidenceFeedback to AdaptiveMissionSelectionEngine.
Ensures verified mission execution outcomes (Run 1) update persistent failure patterns and
risk weights so subsequent candidate selection (Run 2) changes deterministically based
on evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Any, Sequence

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine, CandidateDecisionPacket
from sage.core.outcome_reconciliation import OutcomeReconciliation, OutcomeReconciliationStatus


@dataclass(frozen=True)
class CCLFeedbackRecord:
    """Feedback record generated from a reconciled outcome."""

    decision_id: str
    context_id: str
    reconciliation_digest: str
    status: OutcomeReconciliationStatus
    risk_adjustment: float
    forbidden_paths: tuple[str, ...] = ()
    timestamp: float = field(default_factory=time.time)


class CCLOutcomeFeedbackBridge:
    """Bridge ingesting outcome reconciliations and updating adaptive mission selection risk profiles."""

    def __init__(
        self,
        selection_engine: AdaptiveMissionSelectionEngine | None = None,
    ):
        self.selection_engine = selection_engine or AdaptiveMissionSelectionEngine()
        self.feedback_records: list[CCLFeedbackRecord] = []
        self.forbidden_path_registry: set[str] = set()

    def process_reconciliation(self, reconciliation: OutcomeReconciliation) -> CCLFeedbackRecord:
        """Process a verified OutcomeReconciliation and create a CCLFeedbackRecord."""
        # Risk adjustment rules:
        # - UNRESOLVED or INDETERMINATE -> +30.0 risk penalty
        # - REPORTED -> +10.0 risk penalty
        # - OBSERVED / RECONCILED -> -5.0 risk adjustment (proven baseline)
        risk_adjustment = 0.0
        forbidden_paths: list[str] = []

        if reconciliation.status in (
            OutcomeReconciliationStatus.UNRESOLVED,
            OutcomeReconciliationStatus.INDETERMINATE,
        ):
            risk_adjustment = 30.0
            if reconciliation.t1_observation_ref:
                forbidden_paths.append(reconciliation.t1_observation_ref)
        elif reconciliation.status == OutcomeReconciliationStatus.REPORTED:
            risk_adjustment = 10.0
        elif reconciliation.status in (
            OutcomeReconciliationStatus.OBSERVED,
            OutcomeReconciliationStatus.RECONCILED,
        ):
            risk_adjustment = -5.0

        for path in forbidden_paths:
            self.forbidden_path_registry.add(path)

        record = CCLFeedbackRecord(
            decision_id=reconciliation.decision_id,
            context_id=reconciliation.context_id,
            reconciliation_digest=reconciliation.reconciliation_digest,
            status=reconciliation.status,
            risk_adjustment=risk_adjustment,
            forbidden_paths=tuple(sorted(forbidden_paths)),
        )
        self.feedback_records.append(record)
        return record

    def evaluate_candidates_with_feedback(
        self,
        raw_candidates: Sequence[dict[str, Any]],
    ) -> list[CandidateDecisionPacket]:
        """Evaluate raw candidates applying cumulative feedback risk adjustments and forbidden path locks."""
        adjusted_candidates = []
        for raw in raw_candidates:
            candidate_copy = dict(raw)
            candidate_id = str(candidate_copy.get("candidate_id") or candidate_copy.get("name") or "").strip()

            # Find matching feedback adjustments for this candidate or context
            matching_adjustments = [
                rec.risk_adjustment for rec in self.feedback_records if rec.decision_id == candidate_id or rec.context_id == candidate_id
            ]
            cumulative_adj = sum(matching_adjustments)

            # Check affected paths against forbidden_path_registry
            affected = candidate_copy.get("affected_paths", [])
            for path in affected:
                if path in self.forbidden_path_registry:
                    # Treat as protected path violation if previously falsified
                    candidate_copy.setdefault("affected_paths", []).append("sage/core/forbidden_path_lock")
                    break

            # Evaluate base packet
            packet = self.selection_engine.evaluate_candidate(candidate_copy)

            # Apply cumulative risk adjustment
            new_risk = min(100.0, max(0.0, packet.risk_score + cumulative_adj))
            updated_packet = CandidateDecisionPacket(
                candidate_id=packet.candidate_id,
                description=packet.description,
                evidence_refs=packet.evidence_refs,
                failure_context=packet.failure_context,
                dependency_context=packet.dependency_context,
                risk_score=new_risk,
                protected_path_intersections=packet.protected_path_intersections,
                verification_requirements=packet.verification_requirements,
                falsification_report=packet.falsification_report,
                is_authorized=False,
            )
            adjusted_candidates.append(updated_packet)

        # Sort key: falsification pass first, then risk score ascending, then candidate_id
        def sort_key(p: CandidateDecisionPacket) -> tuple[int, float, str]:
            passed = p.falsification_report.get("passed", False)
            return (-int(passed), p.risk_score, p.candidate_id)

        return sorted(adjusted_candidates, key=sort_key)
