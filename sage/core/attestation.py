"""SAGE Cryptographic Attestation Layer under SPEK v1.1."""

import hmac
import hashlib
import os
from typing import Optional
from sage.core.models import SPEKReceipt


class CryptographicAttestationProvider:
    """Pluggable cryptographic attestation and authority signing provider."""

    def __init__(self, key_hex: Optional[str] = None):
        # Retrieve key from env variable (production) or use derived test keys
        self.secret_key = (
            key_hex
            or os.getenv("SAGE_ATTESTATION_KEY")
            or hashlib.sha256(b"sage-default-attestation-signing-key-2026").hexdigest()
        ).encode()

    def generate_attestation_signature(self, payload: str) -> str:
        """Generates HMAC-SHA256 signature validating authority over payload.

        Args:
            payload: String representation of payload to sign.

        Returns:
            Hex string of the signature.
        """
        mac = hmac.new(self.secret_key, msg=payload.encode(), digestmod=hashlib.sha256)
        return mac.hexdigest()

    def _get_signing_payload(self, receipt: SPEKReceipt) -> str:
        """Creates a deterministic string representing the receipt state to sign."""
        return f"{receipt.candidate_id}:{receipt.validation_score}:{receipt.timestamp}:{receipt.state}"

    def sign_attestation(self, receipt: SPEKReceipt) -> None:
        """Generates and sets cryptographic signature and hashes for a SPEKReceipt."""
        payload = self._get_signing_payload(receipt)
        sig = self.generate_attestation_signature(payload)
        receipt.attestation_signature = sig
        receipt.receipt_hash = sig

    def verify_attestation(self, receipt: SPEKReceipt) -> bool:
        """Verifies receipt's signature authenticity."""
        payload = self._get_signing_payload(receipt)
        expected = self.generate_attestation_signature(payload)
        return hmac.compare_digest(expected, receipt.attestation_signature)
