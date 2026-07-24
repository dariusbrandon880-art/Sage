"""SAGE Policy Enforcement Kernel (SPEK) v1.1 Lifecycle Engine."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sage.core.boundary import BoundaryEnforcer
from sage.core.compliance import ComplianceEngine
from sage.core.hdg import HDGEngine
from sage.core.attestation import CryptographicAttestationProvider
from sage.core.models import HypothesisNode, Proposal, RuleState


class SpekEngine:
    """The central orchestrator for SAGE SPEK v1.1 control plane operations.

    Coordinated path isolation, state routing, causality validation, and attestation.
    """

    def __init__(
        self,
        config_path: Optional[str | Path] = None,
        vault_path: Optional[str | Path] = None,
        promotion_path: Optional[str | Path] = None,
        rejection_path: Optional[str | Path] = None,
        hdg_path: Optional[str | Path] = None,
    ):
        """Initialize SpekEngine and load configurations."""
        self.config_path = Path(config_path or ".sage/config/runtime.json")

        # Load configurations
        self.config = self._load_config()

        self.evidence_threshold = float(self.config.get("evidence_threshold", 0.7))
        self.csi_threshold = float(self.config.get("csi_threshold", 0.5))
        self.runtime_mode = self.config.get("runtime_mode", "production")

        # Core Components
        self.boundary = BoundaryEnforcer()
        self.attestation = CryptographicAttestationProvider(
            provider_type=self.config.get("attestation_provider", "Mock")
        )
        self.hdg = HDGEngine(storage_path=hdg_path, boundary_enforcer=self.boundary)
        self.compliance = ComplianceEngine(
            vault_path=vault_path,
            promotion_path=promotion_path,
            rejection_path=rejection_path,
            boundary_enforcer=self.boundary,
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load JSON configuration safely."""
        if not self.config_path.exists():
            return {
                "spek_version": "1.1",
                "evidence_threshold": 0.7,
                "csi_threshold": 0.5,
                "attestation_provider": "Mock",
                "runtime_mode": "production",
            }
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def process_proposal(
        self,
        proposal_id: str,
        description: str,
        category: str,
        author: str,
        parent_ids: List[str],
        evidence_refs: List[str],
        validation_score: float,
        contradictions: Optional[List[str]] = None,
        auth_token: Optional[str] = None,
    ) -> Proposal:
        """Ingests, evaluates, validates, and routes a rule proposal.

        Executes the deterministic state lifecycle:
        PROPOSED -> EVALUATED -> VALIDATED -> APPROVED or REJECTED -> ARCHIVED

        Args:
            proposal_id: Unique proposal/rule ID.
            description: Narrative text description.
            category: Domain classification.
            author: Author identifier.
            parent_ids: Parent hypothesis node IDs.
            evidence_refs: Flat list of evidence tags/IDs.
            validation_score: Confidence/evidence rating (0.0 to 1.0).
            contradictions: List of node IDs this hypothesis contradicts.
            auth_token: Boundary mutation security token.

        Returns:
            The final Proposal object reflecting the terminal lifecycle state.
        """
        # Ensure system auth token is valid if writing to protected locations
        actual_token = auth_token or ""

        # Step 1: Initialize Proposal under PROPOSED
        proposal = Proposal(
            proposal_id=proposal_id,
            description=description,
            category=category,
            author=author,
            state=RuleState.PROPOSED,
        )

        # Generate a HDG Trace for the current hypothesis and parent context
        hdg_trace = []
        for pid in parent_ids:
            try:
                parent_node = self.hdg.get_node(pid)
                hdg_trace.append(parent_node.model_dump())
            except KeyError:
                # Missing parent will trigger HDG fail-closed during add_node
                pass

        # Append PROPOSED receipt to immutable ledger
        self._generate_lifecycle_receipt(
            proposal_id=proposal_id,
            state=RuleState.PROPOSED,
            execution_permission=True,
            hdg_trace=hdg_trace,
            auth_token=actual_token,
        )

        # Step 2: Transition to EVALUATED
        if not self.compliance.validate_transition(proposal.state, RuleState.EVALUATED):
            raise ValueError(f"Invalid transition from {proposal.state} to EVALUATED")
        proposal.state = RuleState.EVALUATED

        self._generate_lifecycle_receipt(
            proposal_id=proposal_id,
            state=RuleState.EVALUATED,
            execution_permission=True,
            hdg_trace=hdg_trace,
            auth_token=actual_token,
        )

        # Step 3: Transition to VALIDATED
        if not self.compliance.validate_transition(proposal.state, RuleState.VALIDATED):
            raise ValueError(f"Invalid transition from {proposal.state} to VALIDATED")
        proposal.state = RuleState.VALIDATED

        self._generate_lifecycle_receipt(
            proposal_id=proposal_id,
            state=RuleState.VALIDATED,
            execution_permission=True,
            hdg_trace=hdg_trace,
            auth_token=actual_token,
        )

        # Step 4: Epistemic Causality Node Building and Contradiction / Promotion Checking
        node = HypothesisNode(
            node_id=proposal_id,
            description=description,
            parent_ids=parent_ids,
            evidence_refs=evidence_refs,
            validation_score=validation_score,
            contradictions=contradictions or [],
        )

        # Attempt to inject node into HDG. Fails closed on cycles, missing parents, or self-contradictions
        self.hdg.add_node(node, actual_token)

        # A. Contradiction Detection - Block Execution immediately!
        active_contradictions = self.hdg.check_contradictions(proposal_id)
        if active_contradictions:
            # Block execution, HDG is preserved, but we raise an error
            raise ValueError(
                f"SPEK Execution Blocked: Contradiction detected in HDG causality ancestry path "
                f"involving: {active_contradictions}. Lineage preserved but promotion forbidden."
            )

        # B. Low Evidence Rejection Routing
        is_eligible = self.hdg.is_eligible_for_promotion(proposal_id, self.evidence_threshold)

        if not is_eligible:
            # Low evidence or invalid scores -> Transition to REJECTED
            if not self.compliance.validate_transition(proposal.state, RuleState.REJECTED):
                raise ValueError(f"Invalid transition from {proposal.state} to REJECTED")
            proposal.state = RuleState.REJECTED

            # Persist negative result details
            self.compliance.log_rejection(
                proposal_id=proposal_id,
                reason=f"Validation score {validation_score:.2f} is below evidence threshold {self.evidence_threshold:.2f}",
                auth_token=actual_token,
            )

            # Generate REJECTED signed receipt
            self._generate_lifecycle_receipt(
                proposal_id=proposal_id,
                state=RuleState.REJECTED,
                execution_permission=False,
                hdg_trace=hdg_trace,
                auth_token=actual_token,
            )
        else:
            # C. Promotion and Approval Routing
            if not self.compliance.validate_transition(proposal.state, RuleState.APPROVED):
                raise ValueError(f"Invalid transition from {proposal.state} to APPROVED")
            proposal.state = RuleState.APPROVED

            # Mark node as promoted
            node.is_promoted = True
            self.hdg.nodes[proposal_id] = node
            self.hdg.save_graph(actual_token)

            # Log to promotion queue log
            self.compliance.promote_candidate(
                proposal_id=proposal_id,
                title=description,
                auth_token=actual_token,
            )

            # Generate APPROVED signed receipt
            self._generate_lifecycle_receipt(
                proposal_id=proposal_id,
                state=RuleState.APPROVED,
                execution_permission=True,
                hdg_trace=hdg_trace,
                auth_token=actual_token,
            )

        return proposal

    def _generate_lifecycle_receipt(
        self,
        proposal_id: str,
        state: RuleState,
        execution_permission: bool,
        hdg_trace: List[Dict[str, Any]],
        auth_token: str,
    ) -> None:
        """Helper to create and append signed receipt."""
        receipt_id = f"spek_receipt_{uuid.uuid4().hex[:12]}"
        ts = datetime.now(timezone.utc).isoformat()

        # Base signing payload
        signing_payload = {
            "receipt_id": receipt_id,
            "proposal_id": proposal_id,
            "timestamp": ts,
            "lifecycle_state": state.value,
            "execution_permission": execution_permission,
            "authority_integrity_score": 1.0,  # Simulated authority score
            "hdg_trace": hdg_trace,
        }

        # Calculate a signature using our replaceable provider
        signature = self.attestation.sign(signing_payload)

        # Save to Compliance append-only vault
        self.compliance.append_receipt(
            receipt_id=receipt_id,
            proposal_id=proposal_id,
            state=state,
            execution_permission=execution_permission,
            authority_integrity_score=1.0,
            hdg_trace=hdg_trace,
            signature=signature,
            timestamp=ts,
            auth_token=auth_token,
        )
