"""SAGI Phase 2 Governed Search Loop & Research Explorer.

Implements controlled research exploration, candidate generation, mandatory
Guardian verification, failure memory tracking, and deterministic search receipt emission.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.sagi.state import SAGIState
from sage.experimental.sagi.sagi import CandidateProposal, SAGICandidateGenerator
from sage.experimental.sagi.verifier import SAGIVerifier, VerificationResult
from sage.experimental.sagi.controller import SAGIEvolutionController


class SAGISearchState(BaseModel):
    """Search loop state tracking research exploration metrics."""
    cycle_id: str
    candidate_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    failure_count: int = 0
    search_depth: int = 0
    timestamp: float = Field(default_factory=time.time)


class SAGISearchLoopReceipt(BaseModel):
    """Deterministic research search receipt emitted by SAGISearchLoop."""
    cycle_id: str
    candidates_tested: int
    candidates_approved: int
    candidates_rejected: int
    failure_memory_size: int
    guardian_checks_passed: bool
    identity_anchor: str
    research_only: bool = True
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    receipt_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.receipt_sha256:
            self.receipt_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 hash over search receipt contents."""
        payload = {
            "cycle_id": self.cycle_id,
            "candidates_tested": self.candidates_tested,
            "candidates_approved": self.candidates_approved,
            "candidates_rejected": self.candidates_rejected,
            "failure_memory_size": self.failure_memory_size,
            "guardian_checks_passed": self.guardian_checks_passed,
            "identity_anchor": self.identity_anchor,
            "research_only": self.research_only
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGISearchLoop:
    """Governed Research Search Loop for SAGI Explorer."""

    def __init__(
        self,
        controller: Optional[SAGIEvolutionController] = None,
        max_depth: int = 5
    ):
        self.controller = controller or SAGIEvolutionController()
        self.max_depth = max_depth
        self.search_history: List[SAGISearchLoopReceipt] = []

    def ingest_learning_signal(self, learning_signal: Any) -> Dict[str, Any]:
        """Ingest a SAGICognitiveLearningSignal into search loop candidate memory and failure registry."""
        if not hasattr(learning_signal, "signal_type") or not hasattr(learning_signal, "identity_anchor"):
            raise ValueError("Invalid learning signal: missing required attributes.")

        # Identity anchor verification
        expected_anchor = self.controller.state.identity_anchor.initial_sha256
        if learning_signal.identity_anchor != expected_anchor:
            raise ValueError(
                f"SAGI Learning Ingestion Identity Violation: Anchor '{learning_signal.identity_anchor[:12]}' "
                f"does not match expected loop anchor '{expected_anchor[:12]}'."
            )

        if learning_signal.signal_type == "FAILURE_MEMORY":
            mutation_delta = learning_signal.learning_payload.get("rejected_mutation", {})
            self.controller.generator.record_failure(
                proposal_hash=learning_signal.signal_sha256,
                mutation_delta=mutation_delta,
                failure_reason=learning_signal.interpretation.get("failure_classification", "CLOSED_LOOP_FAILURE"),
            )
            return {
                "status": "FAILURE_MEMORY_INGESTED",
                "failure_memory_size": len(self.controller.generator.failure_memory),
            }
        elif learning_signal.signal_type == "SUCCESS_MEMORY":
            # Success memory registers bounded telemetry context, not generalized execution authority
            return {
                "status": "SUCCESS_MEMORY_INGESTED",
                "confidence": learning_signal.confidence,
                "originating_receipt_id": learning_signal.originating_receipt_id,
            }
        else:
            raise ValueError(f"Unknown learning signal type '{learning_signal.signal_type}'.")

    def run_search_cycle(
        self,
        cycle_id: str,
        candidates_per_cycle: int = 3,
        persona_label: str = "sagi_explorer_agent",
        tier3_metadata: Optional[Dict[str, Any]] = None,
        inject_invalid_candidate: bool = False,
        bypass_guardian_attempt: bool = False
    ) -> SAGISearchLoopReceipt:
        """Execute one governed research search cycle over candidates.

        Enforces mandatory Guardian verification for every candidate.
        If bypass_guardian_attempt is True, fails closed immediately.
        """
        search_state = SAGISearchState(
            cycle_id=cycle_id,
            search_depth=min(len(self.search_history) + 1, self.max_depth)
        )

        # Guardian Bypass Prevention: Unverified candidates cannot enter approved state
        if bypass_guardian_attempt:
            receipt = SAGISearchLoopReceipt(
                cycle_id=cycle_id,
                candidates_tested=0,
                candidates_approved=0,
                candidates_rejected=candidates_per_cycle,
                failure_memory_size=len(self.controller.generator.failure_memory),
                guardian_checks_passed=False,
                identity_anchor=self.controller.state.identity_anchor.initial_sha256,
                research_only=True
            )
            self.search_history.append(receipt)
            return receipt

        # Process candidates through mandatory Guardian verification loop
        for i in range(candidates_per_cycle):
            force_fail = inject_invalid_candidate and (i == candidates_per_cycle - 1)
            evolution_rcpt = self.controller.execute_evolution_cycle(
                persona_label=persona_label,
                tier3_metadata=tier3_metadata,
                force_fail_closed=force_fail
            )

            search_state.candidate_count += 1
            if evolution_rcpt.verification_status == "APPROVED":
                search_state.accepted_count += 1
            else:
                search_state.rejected_count += 1
                search_state.failure_count += 1

        # Emit deterministic search loop receipt
        receipt = SAGISearchLoopReceipt(
            cycle_id=cycle_id,
            candidates_tested=search_state.candidate_count,
            candidates_approved=search_state.accepted_count,
            candidates_rejected=search_state.rejected_count,
            failure_memory_size=len(self.controller.generator.failure_memory),
            guardian_checks_passed=True,
            identity_anchor=self.controller.state.identity_anchor.initial_sha256,
            research_only=True
        )

        self.search_history.append(receipt)
        return receipt
