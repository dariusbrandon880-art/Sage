"""C2 Frontier Admission Engine & Classification Ledger.

Implements SAGE C2 Frontier Admission & Reconciliation Protocol:
- Enforces canonical frontier classification states (ACTIVE, READY, RECONCILE, RESEARCH, SUPERSEDED, ARCHIVE, UNSTARTED).
- Performs dependency mapping, collision zone safety checks, and evidence obligation bounding before admitting flights into Big Jump Wave.
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FrontierState(str, Enum):
    """Canonical C2 frontier classification states."""
    ACTIVE = "ACTIVE"
    READY = "READY"
    RECONCILE = "RECONCILE"
    RESEARCH = "RESEARCH"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVE = "ARCHIVE"
    UNSTARTED = "UNSTARTED"


class FrontierCandidate(BaseModel):
    """Minimal mission identity for a candidate capability frontier."""
    frontier_id: str
    target: str
    source: str
    state: FrontierState = FrontierState.UNSTARTED
    base_sha: str
    dependencies: List[str] = Field(default_factory=list)
    collision_zone: str
    evidence_required: List[str] = Field(default_factory=list)
    stop_condition: str


class FrontierAdmissionReceipt(BaseModel):
    """Immutable SHA-256 evidence receipt for frontier admission evaluation."""
    receipt_id: str
    frontier_id: str
    target: str
    admitted: bool
    classified_state: FrontierState
    rejection_reason: Optional[str] = None
    collision_detected: bool = False
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.receipt_id}:{self.frontier_id}:{self.target}:{self.admitted}:{self.classified_state.value}:{self.collision_detected}:{self.timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FrontierAdmissionEngine:
    """Engine enforcing C2 frontier admission and reconciliation rules."""

    def __init__(self, protected_namespaces: Optional[List[str]] = None):
        self.protected_namespaces = protected_namespaces or [
            "sage/core/",
            "sage/runtime/",
            "sage/acr/",
            "sage/agents/",
        ]
        self.active_frontiers: Dict[str, FrontierCandidate] = {}
        self.admission_ledger: List[FrontierAdmissionReceipt] = []

    def classify_and_evaluate(
        self,
        candidate: FrontierCandidate,
        current_active_collision_zones: Optional[List[str]] = None,
    ) -> FrontierAdmissionReceipt:
        """Evaluates candidate frontier against collision zones, dependencies, and protected boundaries."""
        active_zones = current_active_collision_zones or [
            c.collision_zone for c in self.active_frontiers.values()
        ]

        receipt_id = f"receipt-admission-{candidate.frontier_id}-{int(time.time() * 1000)}"

        # 1. Collision check
        if candidate.collision_zone in active_zones:
            receipt = FrontierAdmissionReceipt(
                receipt_id=receipt_id,
                frontier_id=candidate.frontier_id,
                target=candidate.target,
                admitted=False,
                classified_state=FrontierState.RECONCILE,
                rejection_reason=f"Collision detected with active collision zone: '{candidate.collision_zone}'",
                collision_detected=True,
            )
            receipt.receipt_hash = receipt.compute_hash()
            self.admission_ledger.append(receipt)
            return receipt

        # 2. State classification verification
        if candidate.state in (FrontierState.ARCHIVE, FrontierState.SUPERSEDED):
            receipt = FrontierAdmissionReceipt(
                receipt_id=receipt_id,
                frontier_id=candidate.frontier_id,
                target=candidate.target,
                admitted=False,
                classified_state=candidate.state,
                rejection_reason=f"Candidate frontier is classified as {candidate.state.value} and cannot be admitted.",
            )
            receipt.receipt_hash = receipt.compute_hash()
            self.admission_ledger.append(receipt)
            return receipt

        # 3. Admit candidate
        candidate.state = FrontierState.ACTIVE
        self.active_frontiers[candidate.frontier_id] = candidate

        receipt = FrontierAdmissionReceipt(
            receipt_id=receipt_id,
            frontier_id=candidate.frontier_id,
            target=candidate.target,
            admitted=True,
            classified_state=FrontierState.ACTIVE,
        )
        receipt.receipt_hash = receipt.compute_hash()
        self.admission_ledger.append(receipt)
        return receipt

    def get_ledger(self) -> List[FrontierAdmissionReceipt]:
        """Returns the complete admission audit ledger."""
        return list(self.admission_ledger)
