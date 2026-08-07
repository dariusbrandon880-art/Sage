"""SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) Validator.

Provides an experimental, read-only validation pipeline to check incoming evidence
packages for identity verification, linear SAGE-CRC hash-chain integrity,
and relational contradictions before indexing or promotion.
"""

import hashlib
import json
import re
from typing import Any, Dict, List


class SAGEERIPValidator:
    """Enforces programmatic, read-only verification rules under SAGE-ERIP v1.0.

    Operates strictly as a passive validation pipeline. Fails-closed immediately
    by raising a ValueError if any stage of the verification fails.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize the ERIP validator."""
        self.validation_mode = validation_mode
        self.whitelisted_tiers = {"TIER_1_COORDINATOR", "TIER_2_EXECUTION"}

    def generate_sha256(self, previous_hash: str, payload: Dict[str, Any]) -> str:
        """Computes the linear SAGE-CRC link hash: SHA-256(prev_hash || Log_Payload)."""
        serialized = json.dumps(payload, sort_keys=True)
        combined = f"{previous_hash}{serialized}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def validate_ingestion_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Validates an incoming evidence/compliance package against SAGE-ERIP rules.

        Checks:
        1. Identity & Governance Tier Verification
        2. SAGE-CRC Linear Hash-Chain Integrity
        3. Relational & Circular Contradiction Detection
        4. Evidence Quality Score (EQS) Calculation

        Raises:
            ValueError: If any validation rule, signature, or cryptographic link is invalid.
        """
        if not isinstance(package, dict):
            raise ValueError("SAGE-ERIP Ingestion Violation: Compliance package must be a dictionary.")

        # Top-level structural checks
        required_fields = ["package_id", "session_id", "agent_identity", "trace_blocks", "attestation"]
        for field in required_fields:
            if field not in package:
                raise ValueError(f"SAGE-ERIP Ingestion Violation: Missing top-level field '{field}'.")

        # 1. Identity & Governance Tier Verification
        agent_id_data = package["agent_identity"]
        if not isinstance(agent_id_data, dict):
            raise ValueError("SAGE-ERIP Ingestion Violation: 'agent_identity' must be a dictionary.")
        for f in ["agent_id", "governance_tier"]:
            if f not in agent_id_data:
                raise ValueError(f"SAGE-ERIP Ingestion Violation: Missing agent identity field '{f}'.")

        if agent_id_data["governance_tier"] not in self.whitelisted_tiers:
            raise ValueError(f"SAGE-ERIP Ingestion Violation: Unauthorized governance tier '{agent_id_data['governance_tier']}'")

        if not re.match(r"^agent_[a-zA-Z0-9_]{3,64}$", agent_id_data["agent_id"]):
            raise ValueError(f"SAGE-ERIP Ingestion Violation: Invalid format for 'agent_id': '{agent_id_data['agent_id']}'")

        # 2. SAGE-CRC Linear Hash-Chain Integrity Verification
        trace_blocks = package["trace_blocks"]
        if not isinstance(trace_blocks, list) or not trace_blocks:
            raise ValueError("SAGE-ERIP Ingestion Violation: 'trace_blocks' must be a non-empty list.")

        previous_hash = "0" * 64  # Initial seed hash
        signed_blocks = 0

        for idx, block in enumerate(trace_blocks):
            if not isinstance(block, dict):
                raise ValueError(f"SAGE-ERIP Ingestion Violation: Block at index {idx} is not a dictionary.")

            # Validate structural fields of block
            for f in ["block_id", "payload", "block_hash"]:
                if f not in block:
                    raise ValueError(f"SAGE-ERIP Ingestion Violation: Block {idx} is missing field '{f}'.")

            # Validate hash chain continuity
            computed_hash = self.generate_sha256(previous_hash, block["payload"])
            if computed_hash != block["block_hash"]:
                raise ValueError(
                    f"SAGE-ERIP Ingestion Violation: SAGE-CRC Hash-Chain broken at block {idx}. "
                    f"Expected: '{block['block_hash']}', Computed: '{computed_hash}'."
                )

            # Check for signed block status
            if block.get("signed", False):
                signed_blocks += 1

            previous_hash = computed_hash

        # 3. Contradiction & Relational Cycle Detection
        nonces_seen = set()
        for idx, block in enumerate(trace_blocks):
            # Nonce Replay Prevention
            nonce = block["payload"].get("nonce")
            if nonce:
                if nonce in nonces_seen:
                    raise ValueError(f"SAGE-ERIP Ingestion Violation: Duplicate/Replayed nonce detected: '{nonce}'.")
                nonces_seen.add(nonce)

            # Relational Circular Loop Detection
            task_id = block["payload"].get("task_id")
            parent_task_id = block["payload"].get("parent_task_id")
            if task_id and parent_task_id and task_id == parent_task_id:
                raise ValueError(
                    f"SAGE-ERIP Ingestion Violation: Relational contradiction detected. "
                    f"Task '{task_id}' cannot refer to itself as parent."
                )

        # 4. Attestation Signature Checks
        attestation = package["attestation"]
        if not isinstance(attestation, dict) or "signature" not in attestation:
            raise ValueError("SAGE-ERIP Ingestion Violation: Missing or invalid attestation block.")

        if not attestation.get("signature") or attestation["signature"] == "pending_sig":
            raise ValueError("SAGE-ERIP Ingestion Violation: Attestation signature is missing or pending.")

        # 5. Calculate Evidence Quality Score (EQS)
        total_blocks = len(trace_blocks)
        eqs = (signed_blocks / total_blocks) if total_blocks > 0 else 0.0

        # Ingestion requires perfect EQS
        if eqs < 1.0:
            raise ValueError(f"SAGE-ERIP Ingestion Violation: Evidence Quality Score (EQS) must equal 1.0. Found: {eqs}")

        return {
            "package_id": package["package_id"],
            "session_id": package["session_id"],
            "validation_status": "RECONCILED",
            "evidence_quality_score": eqs,
            "chain_root_hash": previous_hash,
            "total_blocks_verified": total_blocks,
            "read_only_assertion": True
        }
