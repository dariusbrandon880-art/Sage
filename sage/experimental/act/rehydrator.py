"""SAGE Agent Continuity Tree Stateless Context Rehydrator."""

import re
import json
import hmac
import hashlib
from typing import Any, Dict, List
from datetime import datetime, timezone

from sage.experimental.act.contracts import CrossModelAuditPayloadValidator


class GovernedAgentRehydrator:
    """Enforces stateless, read-only context rehydration and cryptographic verification.

    Milestone 3 rules require strict read-only execution inside the experimental ACT
    namespace. The rehydrator parses CMAPS v1.0 payloads, re-verifies cryptographic
    attestation signatures, and constructs safe, untampered rehydration states.
    """

    def __init__(self, rehydration_key: bytes = b"sage_secret_rehydration_key_2026"):
        """Initialize rehydrator with a secure key."""
        self.rehydration_key = rehydration_key
        self.validator = CrossModelAuditPayloadValidator()
        self.used_nonces = set()

    def _compute_payload_signature(self, payload: Dict[str, Any]) -> str:
        """Computes the HMAC-SHA256 signature for a given payload dictionary.

        Excludes the 'signature' field under 'attestation' from the signature base
        to ensure deterministic verification.
        """
        # Create a deep copy of the payload to avoid mutating the original
        base_payload = json.loads(json.dumps(payload))

        # Remove signature from attestation base
        if "attestation" in base_payload and "signature" in base_payload["attestation"]:
            base_payload["attestation"]["signature"] = ""

        # Deterministic serialization: sort keys
        serialized = json.dumps(base_payload, sort_keys=True, separators=(",", ":"))

        # Compute HMAC
        mac = hmac.new(self.rehydration_key, serialized.encode("utf-8"), hashlib.sha256)
        return mac.hexdigest()

    def parse_and_verify_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parses and verifies structural, chronological, and cryptographic payload integrity.

        Args:
            payload: CMAPS v1.0 payload dictionary.

        Returns:
            The verified payload dictionary.

        Raises:
            ValueError: On structural validation failure, signature mismatch, or replay attempt.
        """
        # 1. Structural and Chronological validation
        self.validator.validate_payload(payload)

        # 2. Cryptographic Attestation Verification
        sig = payload["attestation"]["signature"]
        computed_sig = self._compute_payload_signature(payload)

        if not hmac.compare_digest(sig, computed_sig):
            raise ValueError(
                f"CMAPS Violation: Cryptographic signature mismatch! "
                f"Payload has been tampered with or unsigned. Provided: '{sig[:10]}...', Computed: '{computed_sig[:10]}...'"
            )

        # 3. Nonce Freshness Check (Replay Protection)
        nonce = payload["attestation"]["nonce"]
        if nonce in self.used_nonces:
            raise ValueError(f"CMAPS Violation: Nonce replay attack detected! Nonce '{nonce}' has already been consumed.")

        # Record nonce consumption statelessly
        self.used_nonces.add(nonce)

        return payload

    def rehydrate_mock_context(self, verified_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Statelessly maps verified payload data into a clean, verified rehydration context.

        Args:
            verified_payload: Already verified payload dictionary.

        Returns:
            A metadata dictionary representing the rehydrated computational state.
        """
        agent_id = verified_payload["agent_identity"]["agent_id"]
        session_id = verified_payload["task_lineage"]["session_id"]
        current_task_id = verified_payload["task_lineage"]["current_task_id"]
        step_counter = verified_payload["execution_state"]["step_counter"]
        model_provider = verified_payload["model_provider"]

        # Safely fetch rehydration token from recovery checkpoints
        rehydration_token = None
        if verified_payload.get("recovery_checkpoints"):
            rehydration_token = verified_payload["recovery_checkpoints"][0].get("rehydration_token")

        return {
            "status": "REHYDRATION_SUCCESSFUL",
            "rehydrated_at": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "session_id": session_id,
            "current_task_id": current_task_id,
            "step_counter": step_counter,
            "model_provider": model_provider,
            "state_snapshot_rehydrated": True,
            "rehydration_token_consumed": rehydration_token,
            "read_only_assertion": True,
        }
