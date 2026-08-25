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
    """Feedback record generated from a reconciled outcome with cryptographic lineage binding."""

    cycle_id: str
    parent_cycle_id: str
    decision_id: str
    context_id: str
    reconciliation_digest: str
    source_outcome_ref: str
    status: OutcomeReconciliationStatus
    risk_adjustment: float
    forbidden_paths: tuple[str, ...] = ()
    measurement_digest: str = ""
    timestamp: float = field(default_factory=time.time)

    def digest(self) -> str:
        payload = {
            "cycle_id": self.cycle_id,
            "parent_cycle_id": self.parent_cycle_id,
            "decision_id": self.decision_id,
            "context_id": self.context_id,
            "reconciliation_digest": self.reconciliation_digest,
            "source_outcome_ref": self.source_outcome_ref,
            "status": self.status.value if isinstance(self.status, OutcomeReconciliationStatus) else str(self.status),
            "risk_adjustment": self.risk_adjustment,
            "forbidden_paths": sorted(self.forbidden_paths),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def verify_lineage(self) -> bool:
        """Verify that record has non-empty cycle lineage and valid digests."""
        if not self.cycle_id.strip() or not self.parent_cycle_id.strip():
            return False
        if len(self.reconciliation_digest) != 64:
            return False
        return True


class CCLOutcomeFeedbackBridge:
    """Bridge ingesting outcome reconciliations and updating adaptive mission selection risk profiles."""

    def __init__(
        self,
        selection_engine: AdaptiveMissionSelectionEngine | None = None,
    ):
        self.selection_engine = selection_engine or AdaptiveMissionSelectionEngine()
        self.feedback_records: list[CCLFeedbackRecord] = []
        self.forbidden_path_registry: set[str] = set()

    def process_reconciliation(
        self,
        reconciliation: OutcomeReconciliation,
        cycle_id: str = "cycle-1",
        parent_cycle_id: str = "cycle-0",
    ) -> CCLFeedbackRecord:
        """Process a verified OutcomeReconciliation and create a lineage-bound CCLFeedbackRecord."""
        if not reconciliation or not reconciliation.reconciliation_digest:
            raise ValueError("OutcomeReconciliation with valid reconciliation_digest required")

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

        measurement_payload = f"{reconciliation.decision_id}:{reconciliation.status.value}:{risk_adjustment}"
        measurement_digest = hashlib.sha256(measurement_payload.encode("utf-8")).hexdigest()

        record = CCLFeedbackRecord(
            cycle_id=cycle_id,
            parent_cycle_id=parent_cycle_id,
            decision_id=reconciliation.decision_id,
            context_id=reconciliation.context_id,
            reconciliation_digest=reconciliation.reconciliation_digest,
            source_outcome_ref=reconciliation.outcome_ref,
            status=reconciliation.status,
            risk_adjustment=risk_adjustment,
            forbidden_paths=tuple(sorted(forbidden_paths)),
            measurement_digest=measurement_digest,
        )

        if not record.verify_lineage():
            raise ValueError("Generated CCLFeedbackRecord failed lineage verification")

        self.feedback_records.append(record)
        return record

    def evaluate_candidates_with_feedback(
        self,
        raw_candidates: Sequence[dict[str, Any]],
        active_cycle_id: str = "cycle-2",
    ) -> list[CandidateDecisionPacket]:
        """Evaluate raw candidates applying cumulative lineage-verified feedback risk adjustments."""
        adjusted_candidates = []
        for raw in raw_candidates:
            candidate_copy = dict(raw)
            candidate_id = str(candidate_copy.get("candidate_id") or candidate_copy.get("name") or "").strip()

            # Find matching verified feedback adjustments for this candidate or context
            matching_adjustments = [
                rec.risk_adjustment
                for rec in self.feedback_records
                if rec.verify_lineage() and (rec.decision_id == candidate_id or rec.context_id == candidate_id)
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
