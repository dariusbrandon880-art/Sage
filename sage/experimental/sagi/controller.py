"""SAGI Evolution Controller & Receipt Engine.

Regulates bounded evolution across candidate generation, verification,
temperature adaptation, failure learning metrics, and fresh receipt emission.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.sagi.state import SAGIState
from sage.experimental.sagi.sagi import CandidateProposal, SAGICandidateGenerator
from sage.experimental.sagi.verifier import SAGIVerifier, VerificationResult


class SAGIEvolutionReceipt(BaseModel):
    """Execution receipt emitted for a SAGI evolution cycle."""
    receipt_id: str
    cycle_index: int
    parent_state_hash: str
    next_state_hash: str
    proposal_id: str
    proposal_hash: str
    verification_status: str
    decision_reasoning: str
    temperature_before: float
    temperature_after: float
    mutation_radius: float
    crpl_f1_passed: bool
    crpl_f2_passed: bool
    failure_memory_count: int
    learning_metrics: Dict[str, float]
    timestamp: float = Field(default_factory=time.time)
    receipt_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.receipt_sha256:
            self.receipt_sha256 = self.compute_sha256()

    def _integrity_payload(self) -> Dict[str, Any]:
        """Return the complete receipt payload excluding only its integrity hash."""
        return {
            "receipt_id": self.receipt_id,
            "cycle_index": self.cycle_index,
            "parent_state_hash": self.parent_state_hash,
            "next_state_hash": self.next_state_hash,
            "proposal_id": self.proposal_id,
            "proposal_hash": self.proposal_hash,
            "verification_status": self.verification_status,
            "decision_reasoning": self.decision_reasoning,
            "temperature_before": self.temperature_before,
            "temperature_after": self.temperature_after,
            "mutation_radius": self.mutation_radius,
            "crpl_f1_passed": self.crpl_f1_passed,
            "crpl_f2_passed": self.crpl_f2_passed,
            "failure_memory_count": self.failure_memory_count,
            "learning_metrics": self.learning_metrics,
            "timestamp": self.timestamp,
        }

    def compute_sha256(self) -> str:
        """Compute SHA-256 over every receipt field except receipt_sha256 itself."""
        serialized = json.dumps(
            self._integrity_payload(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Return whether the stored receipt hash matches its complete payload."""
        return self.receipt_sha256 == self.compute_sha256()


class SAGIEvolutionController:
    """Controller regulating bounded SAGI evolution cycles."""

    def __init__(
        self,
        initial_state: Optional[SAGIState] = None,
        generator: Optional[SAGICandidateGenerator] = None,
        verifier: Optional[SAGIVerifier] = None
    ):
        self.state = initial_state or SAGIState.initialize_genesis()
        self.generator = generator or SAGICandidateGenerator()
        self.verifier = verifier or SAGIVerifier()
        self.receipt_history: List[SAGIEvolutionReceipt] = []
        self.successful_cycles = 0
        self.failed_cycles = 0

    def compute_learning_metrics(self) -> Dict[str, float]:
        """Compute failure learning and evolution metrics (PHASE-1H)."""
        total_cycles = self.successful_cycles + self.failed_cycles
        success_rate = (self.successful_cycles / total_cycles) if total_cycles > 0 else 1.0
        failure_rate = (self.failed_cycles / total_cycles) if total_cycles > 0 else 0.0

        return {
            "total_cycles": float(total_cycles),
            "successful_cycles": float(self.successful_cycles),
            "failed_cycles": float(self.failed_cycles),
            "success_rate": round(success_rate, 4),
            "failure_learning_index": round(1.0 - failure_rate, 4),
            "failure_memory_size": float(len(self.generator.failure_memory))
        }

    def execute_evolution_cycle(
        self,
        persona_label: str = "sagi_core_agent",
        tier3_metadata: Optional[Dict[str, Any]] = None,
        force_fail_closed: bool = False
    ) -> SAGIEvolutionReceipt:
        """Execute one bounded evolution cycle: Generate -> Verify -> Adapt -> Receipt."""
        temp_before = self.state.temperature
        parent_hash = self.state.current_hash

        candidate = self.generator.generate_candidate(
            current_state=self.state,
            proposal_id_prefix=f"sagi_cycle_{self.state.cycle_index}",
            persona_label=persona_label,
            tier3_metadata=tier3_metadata
        )

        if force_fail_closed:
            candidate.mutation_delta["parameter_shift"] = 999.0

        v_result = self.verifier.verify_proposal(self.state, candidate)

        if v_result.is_valid:
            self.successful_cycles += 1
            self.state.temperature = max(0.05, round(self.state.temperature * 0.95, 4))
            self.state.cycle_index += 1
            self.state.active_hypotheses.append({
                "proposal_id": candidate.proposal_id,
                "mutation_delta": candidate.mutation_delta,
                "accepted_at_cycle": self.state.cycle_index
            })
            self.state.update_hash()
        else:
            self.failed_cycles += 1
            self.generator.record_failure(candidate, v_result.decision_reasoning)
            self.state.failure_memory.append({
                "proposal_id": candidate.proposal_id,
                "reason": v_result.decision_reasoning
            })
            self.state.temperature = min(1.8, round(self.state.temperature * 1.05, 4))
            self.state.update_hash()

        learning_metrics = self.compute_learning_metrics()
        receipt = SAGIEvolutionReceipt(
            receipt_id=f"rcpt_sagi_{self.state.cycle_index}_{len(self.receipt_history)+1}",
            cycle_index=self.state.cycle_index,
            parent_state_hash=parent_hash,
            next_state_hash=self.state.current_hash,
            proposal_id=candidate.proposal_id,
            proposal_hash=candidate.proposal_hash,
            verification_status=v_result.status,
            decision_reasoning=v_result.decision_reasoning,
            temperature_before=temp_before,
            temperature_after=self.state.temperature,
            mutation_radius=self.state.mutation_radius,
            crpl_f1_passed=v_result.crpl_f1_passed,
            crpl_f2_passed=v_result.crpl_f2_passed,
            failure_memory_count=len(self.generator.failure_memory),
            learning_metrics=learning_metrics
        )

        self.receipt_history.append(receipt)
        return receipt
