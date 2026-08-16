"""SAGI Closed-Loop Cognitive Learning V1 Engine.

Extends the SAGI cognitive bridge by converting completed mission outcomes (MissionProgressionReceipt)
into explicit, identity-anchored, provenance-preserving learning signals (SAGICognitiveLearningSignal)
that update candidate generation failure/success memory without granting unauthorized execution authority.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.progression import MissionProgressionReceipt, MissionProgressionState
from sage.experimental.sagi.research_graph import SAGIResearchNode, SAGIResearchGraph


class SAGICognitiveLearningSignal(BaseModel):
    """Immutable learning signal generated from a validated mission outcome receipt."""

    signal_id: str
    originating_receipt_id: str
    mission_id: str
    outcome_type: str  # "SUCCESS" | "FAILURE"
    signal_type: str   # "SUCCESS_MEMORY" | "FAILURE_MEMORY"
    identity_anchor: str
    interpretation: Dict[str, Any] = Field(default_factory=dict)
    learning_payload: Dict[str, Any] = Field(default_factory=dict)
    evidence_references: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    signal_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.signal_sha256:
            self.signal_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 hash across learning signal payload."""
        payload = {
            "signal_id": self.signal_id,
            "originating_receipt_id": self.originating_receipt_id,
            "mission_id": self.mission_id,
            "outcome_type": self.outcome_type,
            "signal_type": self.signal_type,
            "identity_anchor": self.identity_anchor,
            "interpretation": self.interpretation,
            "learning_payload": self.learning_payload,
            "evidence_references": sorted(self.evidence_references),
            "confidence": self.confidence,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGICognitiveLearningEngine:
    """Governed engine converting mission outcome receipts into cognitive learning signals."""

    def __init__(self, research_graph: Optional[SAGIResearchGraph] = None):
        self.research_graph = research_graph or SAGIResearchGraph(graph_id="sagi_learning_graph")

    def process_mission_outcome(
        self,
        receipt: MissionProgressionReceipt,
        identity_anchor: str,
        evidence_data: Optional[Dict[str, Any]] = None,
        candidate_generator: Optional[Any] = None,
    ) -> SAGICognitiveLearningSignal:
        """Converts a OUTCOME_CLASSIFIED MissionProgressionReceipt into a validated learning signal."""

        # 1. Provenance & Predecessor Invariant Checks
        if not receipt or not isinstance(receipt, MissionProgressionReceipt):
            raise ValueError("SAGI Learning Engine Rejection: Invalid or missing MissionProgressionReceipt")

        if receipt.next_state != MissionProgressionState.OUTCOME_CLASSIFIED.value:
            raise ValueError(
                f"SAGI Learning Engine Rejection: Receipt state '{receipt.next_state}' "
                f"is not '{MissionProgressionState.OUTCOME_CLASSIFIED.value}'."
            )

        if not receipt.receipt_id or not receipt.signature:
            raise ValueError("SAGI Learning Engine Rejection: Missing receipt_id or signature provenance.")

        # 2. Identity Anchor Boundary Check
        if not identity_anchor or len(identity_anchor) != 64:
            raise ValueError(
                f"SAGI Learning Engine Rejection: Invalid identity anchor '{identity_anchor}'. "
                f"Expected 64-character SHA-256 hex string."
            )

        val_result = receipt.validation_result or {}
        outcome_status = val_result.get("outcome_classification")

        if outcome_status not in ("SUCCESS", "FAILURE"):
            raise ValueError(
                f"SAGI Learning Engine Rejection: Conflicting or invalid outcome classification '{outcome_status}'."
            )

        # 3. Insufficient Evidence Gate
        ev_data = evidence_data or {}
        if ev_data.get("evidence_status") == "INSUFFICIENT":
            raise ValueError("SAGI Learning Engine Rejection: Insufficient evidence to promote outcome to learning signal.")

        signal_id = f"sig_learn_{receipt.receipt_id[-12:]}"
        evidence_refs = ev_data.get("evidence_references") or [receipt.provenance_reference]

        # 4. Enforce Distinctions & Generate Learning Signals
        if outcome_status == "SUCCESS":
            signal_type = "SUCCESS_MEMORY"
            interpretation = {
                "observed_outcome": "SUCCESS",
                "interpretation_summary": f"Mission '{receipt.mission_id}' completed objectives successfully.",
                "evidence_level": "VERIFIED_SINGLE_MISSION",
            }
            # Evidence-bounded confidence: single mission outcome capped at 0.85
            confidence = min(0.85, float(ev_data.get("confidence", 0.80)))
            learning_payload = {
                "successful_mission_id": receipt.mission_id,
                "reason": receipt.reason,
                "evidence_count": len(evidence_refs),
            }
        else:
            signal_type = "FAILURE_MEMORY"
            interpretation = {
                "observed_outcome": "FAILURE",
                "interpretation_summary": f"Mission '{receipt.mission_id}' failed execution or validation.",
                "failure_classification": val_result.get("reason", "EXECUTION_FAILURE"),
            }
            confidence = 1.0  # Failures are deterministic negative learning
            learning_payload = {
                "failed_mission_id": receipt.mission_id,
                "failure_reason": receipt.reason,
                "rejected_mutation": val_result.get("mutation_delta", {"mission_id": receipt.mission_id}),
            }

            # If candidate generator supplied, record failure into failure memory
            if candidate_generator and hasattr(candidate_generator, "record_failure"):
                mutation_delta = learning_payload["rejected_mutation"]
                candidate_generator.record_failure(
                    proposal_hash=receipt.receipt_id,
                    mutation_delta=mutation_delta,
                    failure_reason=receipt.reason,
                )

        signal = SAGICognitiveLearningSignal(
            signal_id=signal_id,
            originating_receipt_id=receipt.receipt_id,
            mission_id=receipt.mission_id,
            outcome_type=outcome_status,
            signal_type=signal_type,
            identity_anchor=identity_anchor,
            interpretation=interpretation,
            learning_payload=learning_payload,
            evidence_references=evidence_refs,
            confidence=confidence,
        )

        # 5. Emit Research Node to Research Graph
        node = SAGIResearchNode(
            node_id=f"node_learn_{signal.signal_id}",
            cycle_id=f"mission_{receipt.mission_id}",
            identity_anchor=identity_anchor,
            candidate_signature=signal.signal_sha256,
            guardian_result="APPROVED" if outcome_status == "SUCCESS" else "REJECTED",
            measurement_summary={
                "signal_type": signal_type,
                "confidence": confidence,
                "originating_receipt_id": receipt.receipt_id,
            },
            failure_state=interpretation if outcome_status == "FAILURE" else None,
        )
        self.research_graph.add_node(node)

        return signal
