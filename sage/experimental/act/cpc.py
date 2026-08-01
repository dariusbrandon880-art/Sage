"""SAGE Experimental Continuity Proof Chamber (SAGE-CPC) Core."""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List
from sage.experimental.act.contracts import CryptographicSessionReceiptChain


class ContinuityProofChamber:
    """An experimental validation harness to stress test stateless state rehydration.

    Ensures zero-drift context rehydration through rigorous cryptographic and signature checks.
    """

    def __init__(self, validation_mode: str = "strict"):
        self.validation_mode = validation_mode
        self.chain_validator = CryptographicSessionReceiptChain()

    def calculate_state_hash(self, session_data: Dict[str, Any]) -> str:
        """Computes a deterministic SHA-256 footprint hash of session data."""
        # Key-sort to ensure canonical serialization
        canonical_str = json.dumps(session_data, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def capture_state(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Records initial session state, compiling task identities and computing H_pre."""
        required = ["session_id", "active_objectives", "mapped_tasks"]
        for key in required:
            if key not in session_data:
                raise ValueError(f"SAGE-CPC Error: Missing required session attribute '{key}' before capture.")

        state_hash = self.calculate_state_hash(session_data)
        return {
            "session_id": session_data["session_id"],
            "state_hash": state_hash,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metadata_snapshot": {
                "active_objectives": list(session_data["active_objectives"]),
                "mapped_tasks": list(session_data["mapped_tasks"]),
            }
        }

    def simulate_interruption(self, active_session: Dict[str, Any]) -> None:
        """Simulates sudden interruption by clearing active in-memory session mappings."""
        active_session.clear()

    def execute_recovery(self, backup_payload: Dict[str, Any], chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retrieves and restores session state after validating recovery payload and SAGE-CRC chain."""
        # 1. Enforce SAGE-CRC validation checks on the receipt sequence
        self.chain_validator.verify_chain_integrity(chain)

        # 2. Check for missing/corrupted recovery payload parameters
        required = ["session_id", "active_objectives", "mapped_tasks"]
        for key in required:
            if key not in backup_payload:
                raise ValueError(f"SAGE-CPC Error: Recovery payload is corrupted. Missing '{key}'.")

        # Confirm the payload hash of the last SAGE-CRC block matches the payload hash of our recovery backup!
        recalculated_payload_hash = hashlib.sha256(json.dumps(backup_payload, sort_keys=True).encode("utf-8")).hexdigest()
        last_block = chain[-1]
        if recalculated_payload_hash != last_block["payload_hash"]:
            raise ValueError(
                f"SAGE-CPC Error: Cryptographic linkage mismatch. "
                f"Payload hash '{recalculated_payload_hash}' does not match SAGE-CRC chain reference '{last_block['payload_hash']}'."
            )

        # Restore the rehydrated state
        rehydrated_session = {
            "session_id": backup_payload["session_id"],
            "active_objectives": list(backup_payload["active_objectives"]),
            "mapped_tasks": list(backup_payload["mapped_tasks"]),
        }
        return rehydrated_session

    def compare_states(self, pre_state_hash: str, post_session_data: Dict[str, Any]) -> bool:
        """Computes post-recovery state hash and verifies zero context drift (H_pre == H_post)."""
        post_state_hash = self.calculate_state_hash(post_session_data)
        if pre_state_hash != post_state_hash:
            raise ValueError(
                f"SAGE-CPC Error: Critical Rehydration Context Drift Detected! "
                f"Pre-interruption footprint '{pre_state_hash}' does not match post-recovery footprint '{post_state_hash}'."
            )
        return True

    def generate_evidence_package(
        self,
        cpc_run_id: str,
        pre_capture: Dict[str, Any],
        post_session: Dict[str, Any],
        chain_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compiles and returns the structured, approved CPC verification trace."""
        self.compare_states(pre_capture["state_hash"], post_session)

        return {
            "cpc_run_id": f"cpc_{cpc_run_id}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "pre_interruption_state": pre_capture,
            "interruption_trace": {
                "event_type": "PROCESS_KILL_SIMULATION",
                "interrupted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "cache_cleared": True
            },
            "recovery_reference": chain_blocks[-1]["receipt_id"],
            "post_recovery_state": {
                "session_id": post_session["session_id"],
                "state_hash": self.calculate_state_hash(post_session),
                "rehydrated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            "integrity_comparison_result": {
                "match": True,
                "pre_hash": pre_capture["state_hash"],
                "post_hash": self.calculate_state_hash(post_session),
                "context_drift_detected": False
            },
            "human_review_status": "PENDING_HUMAN_SIGN_OFF"
        }
