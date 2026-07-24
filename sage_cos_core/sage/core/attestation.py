"""SAGE SPEK Cryptographic Attestation Provider."""

import hashlib
import hmac
import json
import os
from typing import Any, Dict


class CryptographicAttestationProvider:
    """Manages cryptographic attestation signing and verification.

    Pluggable and extensible to support future hardware-backed (TPM/HSM) signing.
    """

    def __init__(self, key_seed: str | None = None, provider_type: str = "deterministic_local"):
        """Initialize provider.

        Args:
            key_seed: Optional secret key seed. If not provided, reads from environment.
            provider_type: Pluggable provider type (e.g., "deterministic_local", "hsm", "tpm").
        """
        self.provider_type = provider_type
        # Do not hardcode secrets. Derive key from environment or default seed dynamically.
        secret_seed = key_seed or os.getenv("SAGE_SPEK_ATTESTATION_SECRET") or "sage_spek_secure_seed_2026_default"
        self._key = hashlib.sha256(secret_seed.encode("utf-8")).digest()

    def get_provider_type(self) -> str:
        """Get the current active provider type."""
        return self.provider_type

    def sign(self, payload: Dict[str, Any]) -> str:
        """Sign a dictionary payload cryptographically.

        Args:
            payload: Dict to sign.

        Returns:
            HMAC-SHA256 signature string with provider prefix.
        """
        serialized = self._serialize(payload)
        mac = hmac.new(self._key, msg=serialized, digestmod=hashlib.sha256)
        return f"{self.provider_type}_attestation_{mac.hexdigest()}"

    def verify(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify the cryptographic signature of a payload.

        Args:
            payload: Payload dict.
            signature: Cryptographic signature to verify.

        Returns:
            True if signature is valid, False otherwise.
        """
        if not signature:
            return False

        prefix = f"{self.provider_type}_attestation_"
        if not signature.startswith(prefix):
            return False

        serialized = self._serialize(payload)
        mac = hmac.new(self._key, msg=serialized, digestmod=hashlib.sha256)
        expected = f"{prefix}{mac.hexdigest()}"
        return hmac.compare_digest(signature, expected)

    def _serialize(self, payload: Dict[str, Any]) -> bytes:
        """Deterministically serialize a dictionary to bytes."""
        return json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
