"""SAGE EAS-001 Immutable Chained Attestation Receipt Record System."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict
from pydantic import BaseModel, Field

from sage.acr.attestation import AttestationProvider


class EASReceipt(BaseModel):
    """Schema for a single EAS-001 immutable validation/promotion receipt."""

    receipt_id: str
    previous_receipt_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    memory_id: str
    action: str  # e.g., "validate_memory", "promote_validated", "promote_archive"
    content_hash: str
    rules_applied: List[str]
    attestation_signature: str
    provider_type: str


class EASReceiptChain:
    """Manages the persistent append-only chain of EAS-001 receipts."""

    def __init__(self, storage_path: str | Path | None = None, attestation: AttestationProvider | None = None):
        """Initialize receipt chain.

        Args:
            storage_path: Path to the receipts ledger JSON file.
            attestation: Active AttestationProvider instance.
        """
        self.storage_path = Path(storage_path or "sage_data/eas_receipts.json")
        self.attestation = attestation or AttestationProvider()
        self.receipts: List[EASReceipt] = []
        self._load_receipts()

    def _load_receipts(self) -> None:
        """Load receipt history from disk."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.receipts = [EASReceipt(**item) for item in data]
        except Exception:
            pass

    def get_last_receipt_hash(self) -> str:
        """Get the hash of the last receipt in the chain, or genesis hash if empty."""
        if not self.receipts:
            return "0" * 64

        last_receipt = self.receipts[-1]
        serialized = json.dumps(last_receipt.model_dump(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def generate_receipt(
        self,
        memory_id: str,
        action: str,
        content: Dict[str, Any],
        rules_applied: List[str],
    ) -> EASReceipt:
        """Generate, sign, append, and persist a new EAS-001 receipt.

        Args:
            memory_id: ID of the validated memory object.
            action: Action string ("validate_memory", "promote_validated", "promote_archive")
            content: Raw dict content of the object.
            rules_applied: List of validation rules that passed.

        Returns:
            The generated EASReceipt object.
        """
        import uuid
        receipt_id = f"eas_receipt_{uuid.uuid4().hex[:12]}"
        prev_hash = self.get_last_receipt_hash()
        ts = datetime.now(timezone.utc).isoformat()

        serialized_content = json.dumps(content, sort_keys=True, default=str)
        content_hash = hashlib.sha256(serialized_content.encode("utf-8")).hexdigest()

        signing_payload = {
            "receipt_id": receipt_id,
            "previous_receipt_hash": prev_hash,
            "content_hash": content_hash,
            "timestamp": ts,
            "memory_id": memory_id,
            "action": action,
        }
        signature = self.attestation.sign_payload(signing_payload)

        receipt = EASReceipt(
            receipt_id=receipt_id,
            previous_receipt_hash=prev_hash,
            timestamp=ts,
            memory_id=memory_id,
            action=action,
            content_hash=content_hash,
            rules_applied=rules_applied,
            attestation_signature=signature,
            provider_type=self.attestation.get_provider_type(),
        )

        self.receipts.append(receipt)
        self._save_receipts()
        return receipt

    def _save_receipts(self) -> None:
        """Persist the receipt chain to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.storage_path, "w") as f:
                json.dump([r.model_dump() for r in self.receipts], f, indent=2)
        except OSError:
            pass

    def verify_chain_integrity(self) -> bool:
        """Verify the full integrity of the EAS-001 receipt chain.

        Returns:
            True if all receipts have valid signatures and valid back-links, False otherwise.
        """
        if not self.receipts:
            return True

        expected_prev_hash = "0" * 64

        for receipt in self.receipts:
            if receipt.previous_receipt_hash != expected_prev_hash:
                return False

            signing_payload = {
                "receipt_id": receipt.receipt_id,
                "previous_receipt_hash": receipt.previous_receipt_hash,
                "content_hash": receipt.content_hash,
                "timestamp": receipt.timestamp,
                "memory_id": receipt.memory_id,
                "action": receipt.action,
            }
            if not self.attestation.verify_signature(signing_payload, receipt.attestation_signature):
                return False

            serialized = json.dumps(receipt.model_dump(), sort_keys=True)
            expected_prev_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return True

    def clear(self) -> None:
        """Clear all receipts (primarily for testing)."""
        self.receipts.clear()
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except OSError:
                pass
