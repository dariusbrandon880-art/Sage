"""SAGE Compliance & SPEK Lifecycle Engine."""

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sage_cos_core.sage.core.models import EASReceipt, Proposal, HypothesisNode
from sage_cos_core.sage.core.attestation import CryptographicAttestationProvider
from sage_cos_core.sage.core.hdg import HDGEngine


class ComplianceEngine:
    """SPEK Lifecycle & Audit Integrity compliance engine."""

    def __init__(
        self,
        base_dir: str | Path | None = None,
        attestation: CryptographicAttestationProvider | None = None,
        hdg: HDGEngine | None = None,
    ):
        """Initialize compliance engine."""
        self.base_dir = Path(base_dir or ".sage/validation/audit")
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.spek_vault_path = self.base_dir / "spek_vault.json"
        self.negative_results_path = self.base_dir / "negative_results.json"
        self.promotion_queue_path = self.base_dir / "promotion_queue.log"

        self.attestation = attestation or CryptographicAttestationProvider()
        self.hdg = hdg or HDGEngine()
        self._lock = threading.RLock()

        self.receipts: List[EASReceipt] = []
        self.load_receipt_vault()

    def load_receipt_vault(self) -> None:
        """Load and verify the SPEK receipt vault. Fails closed on corruption/tampering."""
        with self._lock:
            if not self.spek_vault_path.exists():
                self.receipts = []
                return

            try:
                with open(self.spek_vault_path, "r") as f:
                    content = f.read().strip()
                    if not content:
                        self.receipts = []
                        return
                    data = json.loads(content)
            except Exception as e:
                raise RuntimeError(f"CRITICAL COMPLIANCE FAILURE: Vault corrupted: {e!s}")

            if not isinstance(data, list):
                raise RuntimeError("CRITICAL COMPLIANCE FAILURE: SPEK receipt vault format is invalid")

            self.receipts = []
            for r_dict in data:
                try:
                    receipt = EASReceipt(
                        receipt_id=r_dict["receipt_id"],
                        timestamp=r_dict["timestamp"],
                        lifecycle_state=r_dict["lifecycle_state"],
                        execution_permission=r_dict["execution_permission"],
                        authority_integrity_score=r_dict["authority_integrity_score"],
                        hdg_trace=r_dict["hdg_trace"],
                        cryptographic_attestation=r_dict["cryptographic_attestation"],
                        receipt_hash=r_dict["receipt_hash"],
                        previous_receipt_hash=r_dict["previous_receipt_hash"],
                    )
                    self.receipts.append(receipt)
                except Exception as e:
                    raise RuntimeError(f"CRITICAL COMPLIANCE FAILURE: Corrupted receipt record: {e!s}")

            # Verify chain integrity immediately
            if not self.verify_chain_integrity():
                raise RuntimeError("CRITICAL COMPLIANCE FAILURE: SPEK receipt vault chain integrity is compromised!")

    def verify_chain_integrity(self) -> bool:
        """Verify the immutable cryptographic back-link chain of EAS-001 audit receipts."""
        if not self.receipts:
            return True

        expected_prev_hash = "0" * 64

        for receipt in self.receipts:
            # 1. Back-link validation
            if receipt.previous_receipt_hash != expected_prev_hash:
                return False

            # 2. Cryptographic Attestation verify
            signing_payload = {
                "receipt_id": receipt.receipt_id,
                "timestamp": receipt.timestamp,
                "lifecycle_state": receipt.lifecycle_state,
                "execution_permission": receipt.execution_permission,
                "authority_integrity_score": receipt.authority_integrity_score,
                "hdg_trace": receipt.hdg_trace,
                "previous_receipt_hash": receipt.previous_receipt_hash,
            }
            if not self.attestation.verify(signing_payload, receipt.cryptographic_attestation):
                return False

            # 3. Hash match verification
            serialized = json.dumps(receipt.__dict__, sort_keys=True)
            # Filter out receipt_hash if it was written into it
            filtered_dict = receipt.__dict__.copy()
            if "receipt_hash" in filtered_dict:
                filtered_dict.pop("receipt_hash")
            serialized_filtered = json.dumps(filtered_dict, sort_keys=True)
            calculated_hash = hashlib.sha256(serialized_filtered.encode("utf-8")).hexdigest()

            if receipt.receipt_hash != calculated_hash:
                return False

            expected_prev_hash = receipt.receipt_hash

        return True

    def get_last_receipt_hash(self) -> str:
        """Get hash of the last receipt in the chain."""
        if not self.receipts:
            return "0" * 64
        return self.receipts[-1].receipt_hash

    def evaluate_and_route_proposal(self, proposal: Proposal, hdg_node: HypothesisNode) -> Tuple[bool, EASReceipt]:
        """Evaluate a proposal's lifecycle, generate EAS-001 receipt, and route accordingly."""
        with self._lock:
            import uuid

            # SPEK v1.1 Evaluation rules
            is_approved = True
            rejection_reasons = []

            # Rule 1: Node validation score must exceed evidence threshold
            if hdg_node.validation_score < 0.8:
                is_approved = False
                rejection_reasons.append(f"Insufficient validation score: {hdg_node.validation_score} < threshold 0.8")

            # Rule 2: There must not be any contradiction markers
            if hdg_node.contradiction_markers:
                is_approved = False
                rejection_reasons.append(f"Contradiction markers detected: {hdg_node.contradiction_markers}")

            # Rule 3: Complete ancestry must be present
            try:
                ancestry = self.hdg.get_ancestry(hdg_node.node_id)
            except Exception as e:
                is_approved = False
                rejection_reasons.append(f"Causality ancestry traversal failed: {e!s}")
                ancestry = []

            # Determine states
            if is_approved:
                proposal.lifecycle_state = "APPROVED"
                execution_permission = True
                authority_integrity_score = 1.0
            else:
                proposal.lifecycle_state = "REJECTED"
                execution_permission = False
                authority_integrity_score = 0.0

            # Construct EAS-001 Receipt elements
            receipt_id = f"spek_receipt_{uuid.uuid4().hex[:12]}"
            timestamp = datetime.now(timezone.utc).isoformat()
            prev_hash = self.get_last_receipt_hash()
            hdg_trace = [hdg_node.node_id] + ancestry

            # Cryptographically sign the core fields to prevent tampering
            signing_payload = {
                "receipt_id": receipt_id,
                "timestamp": timestamp,
                "lifecycle_state": proposal.lifecycle_state,
                "execution_permission": execution_permission,
                "authority_integrity_score": authority_integrity_score,
                "hdg_trace": hdg_trace,
                "previous_receipt_hash": prev_hash,
            }
            attestation_sig = self.attestation.sign(signing_payload)

            # Generate content hash of the receipt fields
            receipt_fields = {
                "receipt_id": receipt_id,
                "timestamp": timestamp,
                "lifecycle_state": proposal.lifecycle_state,
                "execution_permission": execution_permission,
                "authority_integrity_score": authority_integrity_score,
                "hdg_trace": hdg_trace,
                "cryptographic_attestation": attestation_sig,
                "previous_receipt_hash": prev_hash,
            }
            serialized_fields = json.dumps(receipt_fields, sort_keys=True)
            calculated_hash = hashlib.sha256(serialized_fields.encode("utf-8")).hexdigest()

            receipt = EASReceipt(
                receipt_id=receipt_id,
                timestamp=timestamp,
                lifecycle_state=proposal.lifecycle_state,
                execution_permission=execution_permission,
                authority_integrity_score=authority_integrity_score,
                hdg_trace=hdg_trace,
                cryptographic_attestation=attestation_sig,
                receipt_hash=calculated_hash,
                previous_receipt_hash=prev_hash,
            )

            # Persist receipt
            self.receipts.append(receipt)
            self.save_receipt_vault()

            # Handle routing based on result
            if is_approved:
                self._route_to_promotion_queue(proposal, receipt)
            else:
                self._route_to_negative_results(proposal, rejection_reasons, receipt)

            return is_approved, receipt

    def _route_to_promotion_queue(self, proposal: Proposal, receipt: EASReceipt) -> None:
        """Route an approved candidate to the persistent promotion queue."""
        log_entry = {
            "timestamp": receipt.timestamp,
            "proposal_id": proposal.proposal_id,
            "title": proposal.title,
            "receipt_id": receipt.receipt_id,
            "lifecycle_state": "PROMOTION_QUEUE",
        }
        serialized = json.dumps(log_entry)
        try:
            with open(self.promotion_queue_path, "a") as f:
                f.write(serialized + "\n")
        except OSError as e:
            raise RuntimeError(f"Failed to write to promotion queue: {e!s}")

    def _route_to_negative_results(self, proposal: Proposal, reasons: List[str], receipt: EASReceipt) -> None:
        """Write a rejected candidate to negative_results.json atomically."""
        current_negatives = {}
        if self.negative_results_path.exists():
            try:
                with open(self.negative_results_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        current_negatives = json.loads(content)
            except Exception:
                pass

        # Append or update proposal
        current_negatives[proposal.proposal_id] = {
            "proposal_id": proposal.proposal_id,
            "title": proposal.title,
            "rejection_reasons": reasons,
            "receipt_id": receipt.receipt_id,
            "timestamp": receipt.timestamp,
            "hdg_trace": receipt.hdg_trace,
        }

        # Atomic write
        temp_path = self.negative_results_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(current_negatives, f, indent=2)
            temp_path.replace(self.negative_results_path)
        except OSError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to record negative results: {e!s}")

    def save_receipt_vault(self) -> None:
        """Atomically persist the receipt vault to spek_vault.json."""
        self.spek_vault_path.parent.mkdir(parents=True, exist_ok=True)

        serialized_vault = [r.__dict__ for r in self.receipts]
        temp_path = self.spek_vault_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(serialized_vault, f, indent=2)
            temp_path.replace(self.spek_vault_path)
        except OSError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to persist SPEK receipt vault: {e!s}")
