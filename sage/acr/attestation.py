"""SAGE Cryptographic Attestation Provider supporting TPM/HSM/Secure Enclave simulation paths."""

import hashlib
import hmac
import os
from typing import Any


class AttestationProvider:
    """Provides cryptographic attestation and verification.

    Supports TPM, HSM, Secure Enclave, and Mock integration/simulation paths.
    """

    def __init__(self, provider_type: str | None = None, key_seed: str | None = None):
        """Initialize the AttestationProvider.

        Args:
            provider_type: The type of hardware enclave/module to simulate.
                           Must be one of "TPM", "HSM", "SecureEnclave", "Mock".
                           Defaults to the environment variable SAGE_ATTESTATION_PROVIDER, or "Mock".
            key_seed: Optional custom seed to derive hardware-bound keys.
        """
        self.provider_type = (
            provider_type
            or os.getenv("SAGE_ATTESTATION_PROVIDER")
            or "Mock"
        ).upper()

        if self.provider_type not in ("TPM", "HSM", "SECUREENCLAVE", "MOCK"):
            # Normalize and default safely
            self.provider_type = "MOCK"

        # Hardware-bound secret derivation simulation
        base_seed = key_seed or os.getenv("SAGE_ATTESTATION_SEED") or "sage_system_secure_entropy_seed_2026"
        # Combine base seed with the provider type to simulate different hardware keys
        self._hw_key = hashlib.sha256(f"{base_seed}:{self.provider_type}".encode()).digest()

    def get_provider_type(self) -> str:
        """Get the active provider path/type."""
        return self.provider_type

    def sign_payload(self, payload: dict[str, Any]) -> str:
        """Sign a dictionary payload cryptographically.

        Args:
            payload: Dictionary to sign.

        Returns:
            HMAC-SHA256 signature in hexadecimal.
        """
        serialized = self._serialize_payload(payload)
        mac = hmac.new(self._hw_key, msg=serialized, digestmod=hashlib.sha256)
        return f"{self.provider_type.lower()}_attestation_{mac.hexdigest()}"

    def verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """Verify the cryptographic signature of a payload.

        Args:
            payload: Dictionary whose signature is being verified.
            signature: Hex signature to check.

        Returns:
            True if the signature is valid, False otherwise.
        """
        if not signature:
            return False

        # Extract the signature hash part
        prefix = f"{self.provider_type.lower()}_attestation_"
        if not signature.startswith(prefix):
            # If it's a mock check or signature from another provider type, handle it gracefully
            for possible_prefix in ("tpm_attestation_", "hsm_attestation_", "secureenclave_attestation_", "mock_attestation_"):
                if signature.startswith(possible_prefix):
                    # We can simulate multi-provider verification by deriving that provider's key
                    prov_type = possible_prefix.split("_")[0].upper()
                    base_seed = os.getenv("SAGE_ATTESTATION_SEED") or "sage_system_secure_entropy_seed_2026"
                    derived_key = hashlib.sha256(f"{base_seed}:{prov_type}".encode()).digest()
                    serialized = self._serialize_payload(payload)
                    mac = hmac.new(derived_key, msg=serialized, digestmod=hashlib.sha256)
                    expected = f"{possible_prefix}{mac.hexdigest()}"
                    return hmac.compare_digest(signature, expected)
            return False

        serialized = self._serialize_payload(payload)
        mac = hmac.new(self._hw_key, msg=serialized, digestmod=hashlib.sha256)
        expected_signature = f"{prefix}{mac.hexdigest()}"
        return hmac.compare_digest(signature, expected_signature)

    def _serialize_payload(self, payload: dict[str, Any]) -> bytes:
        """Deterministic serialization of a dict for stable hashing."""
        import json
        return json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
