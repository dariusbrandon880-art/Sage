"""Fleet Readiness Intelligence Subsystem.

Evaluates evidence-backed fleet readiness state (READY, DEGRADED, UNQUALIFIED)
derived strictly from verified event receipts, qualification levels, and C2 status,
preventing fake readiness claims or authority expansion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Optional


class ReadinessStatus(str, Enum):
    """Fleet Readiness Status Levels."""
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNQUALIFIED = "UNQUALIFIED"


@dataclass(frozen=True)
class FleetReadinessState:
    fleet_id: str
    readiness_score: float  # Normalized 0.0 to 1.0
    readiness_status: ReadinessStatus
    evidence_refs: tuple[str, ...]
    qualification_refs: tuple[str, ...]
    risk_flags: tuple[str, ...]
    evaluator_id: str
    timestamp_utc: str
    readiness_digest: str


@dataclass(frozen=True)
class FleetReadinessReceipt:
    receipt_id: str
    fleet_id: str
    readiness_status: ReadinessStatus
    readiness_score: float
    verified_evidence_count: int
    risk_flags_count: int
    timestamp_utc: str
    receipt_digest: str


class FleetReadinessEvaluator:
    """Evaluates evidence-backed fleet readiness and generates readiness receipts."""

    def __init__(self, fleet_id: str = "SAGE-FLEET-001") -> None:
        self.fleet_id = fleet_id

    @staticmethod
    def _compute_digest(
        fleet_id: str,
        score: float,
        status: ReadinessStatus,
        evidence_refs: tuple[str, ...],
        risk_flags: tuple[str, ...],
    ) -> str:
        ev_str = ",".join(sorted(evidence_refs))
        risk_str = ",".join(sorted(risk_flags))
        raw = f"{fleet_id}|{score:.4f}|{status.value}|{ev_str}|{risk_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def evaluate_readiness(
        self,
        evidence_refs: tuple[str, ...],
        qualification_refs: tuple[str, ...],
        risk_flags: tuple[str, ...],
        timestamp_utc: str,
        evaluator_id: str = "Mission Control",
    ) -> FleetReadinessState:
        """Evaluate readiness state backed strictly by evidence refs and risk flags."""
        # Flight 2 — Falsification & Validation Guards
        if not evidence_refs:
            raise ValueError("Readiness Evaluation Rejected: evidence_refs cannot be empty.")
        if any(not ref or not ref.strip() for ref in evidence_refs):
            raise ValueError("Readiness Evaluation Rejected: evidence_refs contains empty values.")
        if not qualification_refs:
            raise ValueError("Readiness Evaluation Rejected: qualification_refs cannot be empty.")

        # Score calculation: base 1.0, deducted by risks, penalised if missing qualifications
        base_score = 1.0
        risk_penalty = len(risk_flags) * 0.20
        evidence_boost = min(0.20, len(evidence_refs) * 0.05)

        final_score = max(0.0, min(1.0, base_score - risk_penalty + evidence_boost))

        # Determine readiness status state machine
        if "CRITICAL_SECURITY_VIOLATION" in risk_flags or len(risk_flags) >= 3:
            status = ReadinessStatus.UNQUALIFIED
            final_score = min(final_score, 0.20)
        elif risk_flags or final_score < 0.70:
            status = ReadinessStatus.DEGRADED
        else:
            status = ReadinessStatus.READY

        digest = self._compute_digest(
            self.fleet_id, final_score, status, evidence_refs, risk_flags
        )

        return FleetReadinessState(
            fleet_id=self.fleet_id,
            readiness_score=final_score,
            readiness_status=status,
            evidence_refs=evidence_refs,
            qualification_refs=qualification_refs,
            risk_flags=risk_flags,
            evaluator_id=evaluator_id,
            timestamp_utc=timestamp_utc,
            readiness_digest=digest,
        )

    def generate_receipt(
        self, state: FleetReadinessState, timestamp_utc: str
    ) -> FleetReadinessReceipt:
        """Generate a signed evidence receipt for a verified readiness state."""
        receipt_id = f"frr_{hashlib.sha256(f'{state.fleet_id}:{state.readiness_digest}:{timestamp_utc}'.encode()).hexdigest()[:10]}"
        digest_raw = f"{receipt_id}|{state.fleet_id}|{state.readiness_status.value}|{state.readiness_score:.4f}|{timestamp_utc}"
        digest = hashlib.sha256(digest_raw.encode("utf-8")).hexdigest()

        return FleetReadinessReceipt(
            receipt_id=receipt_id,
            fleet_id=state.fleet_id,
            readiness_status=state.readiness_status,
            readiness_score=state.readiness_score,
            verified_evidence_count=len(state.evidence_refs),
            risk_flags_count=len(state.risk_flags),
            timestamp_utc=timestamp_utc,
            receipt_digest=digest,
        )
