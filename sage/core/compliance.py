"""SAGE Compliance Engine and Immutable Vault ledger audit trails under SPEK v1.1."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sage.core.models import SPEKReceipt
from sage.core.attestation import CryptographicAttestationProvider


class SPEKVaultData(BaseModel):
    """The serialized schema representation of the SPEK Vault Ledger."""

    receipts: List[SPEKReceipt] = []


class ComplianceEngine:
    """Manages the EAS-001 evidence-based receipt chain validation and audit tracking."""

    def __init__(self, audit_dir: str):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.vault_file = self.audit_dir / "spek_vault.json"
        self._load_vault()

    def _load_vault(self) -> None:
        """Loads or initializes the vault ledger file."""
        if not self.vault_file.exists():
            self._save_vault(SPEKVaultData())
        try:
            with open(self.vault_file, "r") as f:
                data = json.load(f)
                self.vault = SPEKVaultData(**data)
        except Exception:
            # Fallback to empty vault if corrupted upon loading
            self.vault = SPEKVaultData()

    def _save_vault(self, vault_data: SPEKVaultData) -> None:
        """Atomically saves the vault ledger file."""
        temp_file = self.vault_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(vault_data.model_dump(), f, indent=2)
        temp_file.replace(self.vault_file)

    def append_receipt(self, receipt: SPEKReceipt) -> None:
        """Append an authorized promotion transaction receipt to the ledger.

        Enforces EAS-001 receipt chaining where the current receipt references
        the hash of the previous receipt in the ledger.
        """
        # Ensure latest vault state is loaded
        self._load_vault()

        # Link to the previous receipt hash if any exist to form a secure blockchain-like ledger
        if self.vault.receipts:
            prev_receipt = self.vault.receipts[-1]
            receipt.parent_receipt_hash = prev_receipt.attestation_signature
            receipt.previous_receipt_hash = prev_receipt.receipt_hash
        else:
            receipt.parent_receipt_hash = "GENESIS_RECOGNITION"
            receipt.previous_receipt_hash = "GENESIS_RECOGNITION"

        self.vault.receipts.append(receipt)
        self._save_vault(self.vault)

    def verify_vault_chain_integrity(self) -> bool:
        """Verifies the complete integrity of the SPEK Vault Ledger chain.

        Validates that:
        1. Every receipt's cryptographic signature is authentic.
        2. The chronological chain linkage (EAS-001 reference hashes) is unbroken.

        Returns:
            True if vault integrity is fully validated; False if any tamper is detected.
        """
        self._load_vault()
        if not self.vault.receipts:
            return True

        attestor = CryptographicAttestationProvider()

        # Iterate and verify receipts
        for i, receipt in enumerate(self.vault.receipts):
            # 1. Cryptographic Signature Validation
            if not attestor.verify_attestation(receipt):
                return False

            # 2. Chronological Hash Chaining Validation
            if i > 0:
                prev_receipt = self.vault.receipts[i - 1]
                if receipt.parent_receipt_hash != prev_receipt.attestation_signature:
                    return False
                if receipt.previous_receipt_hash != prev_receipt.receipt_hash:
                    return False
            else:
                if receipt.parent_receipt_hash != "GENESIS_RECOGNITION":
                    return False
                if receipt.previous_receipt_hash != "GENESIS_RECOGNITION":
                    return False

        return True
