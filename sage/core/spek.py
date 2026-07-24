"""SAGE SPEK Policy Enforcement Kernel Core under SPEK v1.1."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from sage.core.models import SPEKLifecycleState, SPEKReceipt
from sage.core.boundary import BoundaryEnforcer
from sage.core.compliance import ComplianceEngine
from sage.core.hdg import HDGCausalityEngine, HDGNode
from sage.core.attestation import CryptographicAttestationProvider


class PolicyEnforcementKernel:
    """The central runtime processor of SPEK (Policy Enforcement Kernel) v1.1."""

    def __init__(self, audit_dir: str):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        self.boundary = BoundaryEnforcer()
        self.compliance = ComplianceEngine(audit_dir=str(self.audit_dir))
        self.hdg = HDGCausalityEngine()
        self.attestor = CryptographicAttestationProvider()

        # Re-register existing immutable nodes from compliance ledger into the HDG Graph
        for receipt in self.compliance.vault.receipts:
            if receipt.state == SPEKLifecycleState.APPROVED:
                node = HDGNode(
                    id=receipt.candidate_id,
                    title=receipt.title,
                    parent_ids=receipt.parent_ids,
                    evidence_references=receipt.evidence_references,
                    validation_score=receipt.validation_score,
                )
                self.hdg.nodes[node.id] = node

    def evaluate_and_promote_candidate(
        self,
        candidate_id: str,
        title: str,
        parent_ids: List[str],
        evidence_references: List[str],
        validation_score: float,
        is_contradicted: bool,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the SPEK promotion pipeline on a SAGE Rule Candidate.

        Steps:
        1. Authorize transition via logical security Boundary Enforcement.
        2. Graph dependencies dynamically & verify trace lineages (HDG Cycle Check).
        3. Evaluate quality thresholds and Epistemic Firewall contradictions.
        4. Generate a secure, cryptographically signed SPEK receipt.
        5. Append approved state mutations to EAS-001 Immutable Compliance Ledger.
        6. Append rejected candidates to the non-mutable negative results tracker.
        """
        # 1. Logical Boundary Enforcement
        try:
            self.boundary.enforce_boundary_mutation(auth_token)
        except PermissionError as e:
            return {
                "success": False,
                "error": f"Security Boundary Violation: {str(e)}",
                "next_state": SPEKLifecycleState.REJECTED,
            }

        # 2. Build the hypothesis node and run HDG validity checks
        node = HDGNode(
            id=candidate_id,
            title=title,
            parent_ids=parent_ids,
            evidence_references=evidence_references,
            validation_score=validation_score,
            is_contradicted=is_contradicted,
        )

        try:
            self.hdg.add_node(node)
        except ValueError as e:
            self._log_negative_result(candidate_id, title, f"HDG Registration Failure: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "next_state": SPEKLifecycleState.REJECTED,
            }

        # 3. Quality threshold and Epistemic contradictions evaluation
        # Require at least one evidence reference for promotion
        has_adequate_evidence = len(evidence_references) > 0
        is_eligible = self.hdg.is_eligible_for_promotion(candidate_id) and has_adequate_evidence

        if is_eligible:
            # Candidate is successfully promoted to Layer 3 (Immutable Ledger)
            receipt = SPEKReceipt(
                candidate_id=candidate_id,
                title=title,
                parent_ids=parent_ids,
                evidence_references=evidence_references,
                validation_score=validation_score,
                timestamp=datetime.now(timezone.utc).isoformat(),
                state=SPEKLifecycleState.APPROVED,
                lifecycle_state=SPEKLifecycleState.APPROVED,
                parent_receipt_hash="",  # Populated inside compliance.append_receipt
                attestation_signature="",  # Populated by sign_attestation
            )

            # Generate Cryptographic HMAC Attestation Signature
            self.attestor.sign_attestation(receipt)

            # Record in compliance ledger
            self.compliance.append_receipt(receipt)

            # Write descriptive transaction action to append-only log
            promotion_log = self.audit_dir / "promotion_queue.log"
            with open(promotion_log, "a") as log:
                log.write(
                    f"[{receipt.timestamp}] Candidate Promoted to Immutable Ledger: ID={candidate_id} Signature={receipt.attestation_signature}\n"
                )

            return {
                "success": True,
                "next_state": SPEKLifecycleState.APPROVED,
                "receipt": receipt.model_dump(),
            }
        else:
            # Candidate fails validation rules, log rejection to negative_results tracker
            fail_reason = "Fails quality index/evidence thresholds or parent contradiction."
            self._log_negative_result(candidate_id, title, fail_reason)

            # Set node to contradicted if it isn't eligible
            self.hdg.flag_contradiction(candidate_id, fail_reason)

            return {
                "success": False,
                "error": fail_reason,
                "next_state": SPEKLifecycleState.REJECTED,
            }

    def _log_negative_result(self, candidate_id: str, title: str, reason: str) -> None:
        """Appends a rejected candidate record to the offline negative results logs."""
        neg_file = self.audit_dir / "negative_results.json"
        data = {"rejected_candidates": []}

        if neg_file.exists():
            try:
                with open(neg_file, "r") as f:
                    data = json.load(f)
            except Exception:
                pass

        data["rejected_candidates"].append({
            "candidate_id": candidate_id,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        })

        with open(neg_file, "w") as f:
            json.dump(data, f, indent=2)
