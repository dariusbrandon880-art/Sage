"""SAGI Verifier & Falsification Engine.

Implements identity invariant verification, spectral stability,
domain bounds enforcement, and CRPL-F1 / CRPL-F2 falsification checks.
"""

from typing import Any, Dict, Tuple
from pydantic import BaseModel

from sage.experimental.sagi.state import SAGIState
from sage.experimental.sagi.sagi import CandidateProposal


class VerificationResult(BaseModel):
    """Result of SAGI candidate verification."""
    is_valid: bool
    status: str
    state_integrity_passed: bool
    identity_invariant_passed: bool
    spectral_stability_passed: bool
    crpl_f1_passed: bool
    crpl_f2_passed: bool
    decision_reasoning: str


class SAGIVerifier:
    """Verifier & Falsification Engine for SAGI proposals."""

    def __init__(self, max_spectral_shift: float = 0.5):
        self.max_spectral_shift = max_spectral_shift

    def verify_proposal(self, state: SAGIState, proposal: CandidateProposal) -> VerificationResult:
        """Run complete verification and falsification battery over candidate proposal."""
        # 0. State Integrity: reject proposals against a mutated/corrupted Ω state.
        state_integrity_passed = state.verify_integrity()

        # 1. Identity Invariant Verification: Parent state hash must match current state hash
        identity_passed = (proposal.parent_state_hash == state.current_hash)

        # 2. Spectral Stability Check: Mutation parameter shift must not exceed max_spectral_shift
        param_shift = abs(proposal.mutation_delta.get("parameter_shift", 0.0))
        spectral_passed = (param_shift <= self.max_spectral_shift)

        # 3. CRPL-F1 Falsification Check: Verify tier3_metadata does NOT alter proposal_hash
        clean_proposal = proposal.model_copy()
        clean_proposal.tier3_metadata = {}
        crpl_f1_passed = (proposal.proposal_hash == clean_proposal.compute_sha256())

        # 4. CRPL-F2 Falsification Check: Verify persona_label does NOT alter proposal_hash
        persona_proposal = proposal.model_copy()
        persona_proposal.persona_label = "alternate_persona_label"
        crpl_f2_passed = (proposal.proposal_hash == persona_proposal.compute_sha256())

        overall_valid = (
            state_integrity_passed
            and identity_passed
            and spectral_passed
            and crpl_f1_passed
            and crpl_f2_passed
        )

        reasons = []
        if not state_integrity_passed:
            reasons.append("STATE_INTEGRITY_VIOLATION: Stored Ω state hash mismatch")
        if not identity_passed:
            reasons.append("IDENTITY_INVARIANT_VIOLATION: Parent state hash mismatch")
        if not spectral_passed:
            reasons.append(f"SPECTRAL_STABILITY_VIOLATION: Shift {param_shift} > max {self.max_spectral_shift}")
        if not crpl_f1_passed:
            reasons.append("CRPL_F1_VIOLATION: Tier 3 metadata influenced semantic proposal hash")
        if not crpl_f2_passed:
            reasons.append("CRPL_F2_VIOLATION: Persona label influenced semantic proposal hash")

        reasoning_str = "; ".join(reasons) if reasons else "ALL_VERIFICATION_AND_FALSIFICATION_CHECKS_PASSED"

        return VerificationResult(
            is_valid=overall_valid,
            status="APPROVED" if overall_valid else "REJECTED",
            state_integrity_passed=state_integrity_passed,
            identity_invariant_passed=identity_passed,
            spectral_stability_passed=spectral_passed,
            crpl_f1_passed=crpl_f1_passed,
            crpl_f2_passed=crpl_f2_passed,
            decision_reasoning=reasoning_str
        )
