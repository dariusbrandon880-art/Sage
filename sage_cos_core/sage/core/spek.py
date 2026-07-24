"""SAGE Policy Enforcement Kernel (SPEK) Orchestrator."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sage_cos_core.sage.core.models import EASReceipt, HypothesisNode, Proposal
from sage_cos_core.sage.core.attestation import CryptographicAttestationProvider
from sage_cos_core.sage.core.boundary import BoundaryEnforcer
from sage_cos_core.sage.core.compliance import ComplianceEngine
from sage_cos_core.sage.core.hdg import HDGEngine


class SAGEPolicyEnforcementKernel:
    """SPEK Core Orchestrator.

    Coordinates the configuration, cryptographic attestation, causality engine,
    and security boundaries to enforce deterministic rules and immutable audits.
    """

    def __init__(self, root_dir: str | Path | None = None, system_token: str | None = None):
        """Initialize the SPEK core platform."""
        self.root_dir = Path(root_dir or ".").resolve()

        # Load configuration
        self.config_path = self.root_dir / "sage_cos_core/.sage/config/runtime.json"
        self.config = self._load_configuration()

        # Secure System Token for path permissions
        self.system_token = system_token or os.getenv("SAGE_SPEK_SYSTEM_TOKEN") or "spek_system_internal_auth_token_2026"

        # Initialize Subsystems
        self.boundary = BoundaryEnforcer(root_dir=self.root_dir)

        # Before initializing HDG and Compliance, we must validate boundary permissions
        self.boundary.validate_write_permission(self.root_dir / "sage_cos_core/.sage", self.system_token)

        self.attestation = CryptographicAttestationProvider(
            provider_type=self.config.get("attestation_provider", "local_deterministic")
        )

        self.hdg_path = self.root_dir / "sage_cos_core/.sage/validation/audit/hdg_causality.json"
        self.hdg = HDGEngine(storage_path=self.hdg_path)

        self.compliance = ComplianceEngine(
            base_dir=self.root_dir / "sage_cos_core/.sage/validation/audit",
            attestation=self.attestation,
            hdg=self.hdg,
        )

    def _load_configuration(self) -> Dict[str, Any]:
        """Load external runtime configuration. Fails closed if config is corrupted."""
        if not self.config_path.exists():
            # Create default inline if not exists
            return {
                "spek_version": "1.1.0",
                "evidence_threshold": 0.8,
                "csi_threshold": 0.9,
                "attestation_provider": "local_deterministic",
                "runtime_mode": "enforcement"
            }

        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"CRITICAL CONFIGURATION CORRUPTION: Failed to parse runtime config: {e!s}")

    def submit_proposal(
        self,
        proposal: Proposal,
        parent_ids: List[str],
        validation_score: float,
        metadata: Dict[str, Any] | None = None,
    ) -> Tuple[bool, EASReceipt]:
        """Process, validate, route, and audit a control/rule proposal through SPEK."""
        # 1. Security Boundary Write Permission validation
        self.boundary.validate_write_permission(self.spek_vault_path(), self.system_token)

        # 2. Add node to HDG causality engine
        node_id = f"node_{proposal.proposal_id}"
        hdg_node = HypothesisNode(
            node_id=node_id,
            parent_ids=parent_ids,
            evidence_references=proposal.evidence_references,
            validation_score=validation_score,
            contradiction_markers=[],
            promotion_eligible=(validation_score >= self.config.get("evidence_threshold", 0.8)),
            metadata=metadata or {},
        )

        # Ancestry is verified here. Missing parents raise ValueError (system fails closed)
        self.hdg.add_node(hdg_node)

        # 3. Route to Lifecycle Engine & Create Receipt
        is_approved, receipt = self.compliance.evaluate_and_route_proposal(proposal, hdg_node)

        return is_approved, receipt

    def spek_vault_path(self) -> Path:
        """Get absolute path to receipt vault."""
        return self.compliance.spek_vault_path

    def verify_vault_integrity(self) -> bool:
        """Verify the full audit chain verification of all receipts in the vault."""
        return self.compliance.verify_chain_integrity()
