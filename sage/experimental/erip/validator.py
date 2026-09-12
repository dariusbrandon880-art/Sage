"""SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) Validation Core."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from sage.core.attestation import CryptographicAttestationProvider
from sage.experimental.act.contracts import CrossModelAuditPayloadValidator
from sage.experimental.cognitive.state_schema import CANONICAL_AUTHORIZED_AGENTS
from sage.experimental.erip.models import (
    ERIPCompliancePack,
    ERIPContradictionFinding,
    ERIPValidationResult,
)


KNOWN_SAGE_AGENT_IDS = set(CANONICAL_AUTHORIZED_AGENTS) | {
    "JULES",
    "CHATGPT",
    "GEMINI",
    "agent_jules_sage",
    "agent_chatgpt_c2",
    "agent_gemini_recon",
    "agent_sagi_core",
}

VALID_GOVERNANCE_TIERS = {"canonical", "experimental", "shadow"}
SPEK_SIG_PREFIXES = ("mock_spek_sig_", "tpm_spek_sig_", "hsm_spek_sig_", "secureenclave_spek_sig_")


class ERIPValidationCore:
    """Executable sandboxed validation core for SAGE-ERIP Milestone 1.

    Enforces 6 sequential validation stages:
    1. Evidence-package intake & CMAPS boundary check
    2. Identity verification (with cryptographic attestation checking)
    3. Integrity verification (SAGE-CRC SHA-256 linear hash chain)
    4. Receipt reconciliation
    5. Contradiction detection
    6. Deterministic validation result generation

    Operates strictly in read-only mode with zero writes to Master Archive or production core.
    """

    def __init__(self, root_dir: Optional[Path] = None, max_age_seconds: float = 86400.0):
        """Initialize ERIP validation core."""
        self.root_dir = root_dir or Path(__file__).parent.parent.parent.parent
        self.max_age_seconds = max_age_seconds
        self.seen_nonces: Set[str] = set()
        self.cmaps_validator = CrossModelAuditPayloadValidator(validation_mode="strict")
        self.attestation_provider = CryptographicAttestationProvider()

    @staticmethod
    def compute_sage_crc_hash_chain(payloads: List[str], seed_hash: Optional[str] = None) -> str:
        """Reconstruct the SAGE-CRC SHA-256 linear hash chain.

        Formula:
            H_0 = seed_hash or SHA256("")
            H_i = SHA256(H_{i-1} || payload_i)
        """
        current_hash = seed_hash or hashlib.sha256(b"").hexdigest()
        for payload in payloads:
            combined = (current_hash + payload).encode("utf-8")
            current_hash = hashlib.sha256(combined).hexdigest()
        return current_hash

    def validate_compliance_pack(
        self, pack: Union[Dict[str, Any], ERIPCompliancePack]
    ) -> ERIPValidationResult:
        """Execute the 6-stage ERIP validation pipeline on an incoming compliance pack."""
        if isinstance(pack, ERIPCompliancePack):
            pack_dict = pack.model_dump()
        else:
            pack_dict = pack

        stages_executed: List[str] = []
        contradictions: List[ERIPContradictionFinding] = []
        integrity_verified = False

        # Extract basic identity context for error reporting
        actor = pack_dict.get("actor_identity", {}) if isinstance(pack_dict.get("actor_identity"), dict) else {}

        # =====================================================================
        # STAGE 1: Intake & CMAPS Boundary Check
        # =====================================================================
        stage_name = "INTAKE_VALIDATION"
        stages_executed.append(stage_name)

        if not isinstance(pack_dict, dict):
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason="Compliance pack input must be a dictionary",
                contradictions=contradictions,
            )

        required_keys = ["actor_identity", "cmaps_payload", "hash_chain", "terminal_root_hash", "nonce", "timestamp"]
        for key in required_keys:
            if key not in pack_dict or pack_dict[key] is None:
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason=f"Malformed compliance pack: missing required field '{key}'",
                    contradictions=contradictions,
                )

        cmaps_payload = pack_dict.get("cmaps_payload")
        try:
            self.cmaps_validator.validate_payload(cmaps_payload)
        except Exception as e:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason=f"CMAPS validation boundary violation: {str(e)}",
                contradictions=contradictions,
            )

        # =====================================================================
        # STAGE 2: Identity Verification
        # =====================================================================
        stage_name = "IDENTITY_VERIFICATION"
        stages_executed.append(stage_name)

        if not isinstance(actor, dict):
            return self._build_reject(
                actor={},
                stages=stages_executed,
                failed_stage=stage_name,
                reason="Actor identity must be a dictionary",
                contradictions=contradictions,
            )

        agent_id = actor.get("agent_id")
        gov_tier = actor.get("governance_tier")
        signature = actor.get("signature")
        key_fingerprint = actor.get("key_fingerprint")

        if not agent_id or agent_id not in KNOWN_SAGE_AGENT_IDS:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason=f"Fail closed: Unknown or unauthorized actor identity '{agent_id}'",
                contradictions=contradictions,
            )

        if not gov_tier or gov_tier not in VALID_GOVERNANCE_TIERS:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason=f"Fail closed: Invalid governance tier '{gov_tier}' for actor identity",
                contradictions=contradictions,
            )

        if not signature or not isinstance(signature, str) or len(signature.strip()) < 8:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason="Fail closed: Missing or invalid cryptographic actor signature",
                contradictions=contradictions,
            )

        if not key_fingerprint or not isinstance(key_fingerprint, str) or len(key_fingerprint.strip()) < 8:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason="Fail closed: Missing or invalid cryptographic key fingerprint",
                contradictions=contradictions,
            )

        # Perform Cryptographic Attestation verification if cryptographic SPEK signature format is present
        signing_payload = {
            "agent_id": agent_id,
            "name": actor.get("name"),
            "role": actor.get("role"),
            "governance_tier": gov_tier,
            "key_fingerprint": key_fingerprint,
        }
        if signature.startswith(SPEK_SIG_PREFIXES):
            if not self.attestation_provider.verify(signing_payload, signature):
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason="Cryptographic signature verification failed: actor identity signature does not match payload digest",
                    contradictions=contradictions,
                )

        # =====================================================================
        # STAGE 3: Integrity Verification (SAGE-CRC Hash Chain)
        # =====================================================================
        stage_name = "INTEGRITY_VERIFICATION"
        stages_executed.append(stage_name)

        hash_chain = pack_dict.get("hash_chain")
        terminal_root_hash = pack_dict.get("terminal_root_hash")

        if not isinstance(hash_chain, list) or not hash_chain:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason="SAGE-CRC Integrity check failed: hash_chain must be a non-empty list of payloads",
                contradictions=contradictions,
            )

        if not terminal_root_hash or not re.match(r"^[a-fA-F0-9]{64}$", str(terminal_root_hash)):
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason="SAGE-CRC Integrity check failed: terminal_root_hash must be a 64-character SHA-256 hex string",
                contradictions=contradictions,
            )

        reconstructed_hash = self.compute_sage_crc_hash_chain(hash_chain)
        if reconstructed_hash != terminal_root_hash:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason=(
                    f"SAGE-CRC hash-chain tampering detected: computed root ({reconstructed_hash}) "
                    f"does not match pack terminal root ({terminal_root_hash})"
                ),
                contradictions=contradictions,
            )

        integrity_verified = True

        # =====================================================================
        # STAGE 4: Receipt Reconciliation
        # =====================================================================
        stage_name = "RECEIPT_RECONCILIATION"
        stages_executed.append(stage_name)

        task_lineage = cmaps_payload.get("task_lineage", {})
        parent_task_id = task_lineage.get("parent_task_id")
        parent_receipt = pack_dict.get("parent_receipt")

        if parent_task_id:
            if not parent_receipt or not isinstance(parent_receipt, dict):
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason=f"Orphaned evidence detected: parent_task_id '{parent_task_id}' specified but parent_receipt is missing",
                    contradictions=contradictions,
                )

            p_task = parent_receipt.get("parent_task_id")
            p_hash = parent_receipt.get("parent_passport_hash")
            p_sig = parent_receipt.get("parent_signature")

            if p_task != parent_task_id:
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason=f"Receipt mismatch: parent_receipt task ('{p_task}') does not match CMAPS parent task ('{parent_task_id}')",
                    contradictions=contradictions,
                )

            if not p_hash or not re.match(r"^[a-fA-F0-9]{64}$", str(p_hash)):
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason="Receipt mismatch: parent_receipt passport hash is missing or invalid SHA-256 hex format",
                    contradictions=contradictions,
                )

            if not p_sig or not isinstance(p_sig, str) or len(p_sig.strip()) < 8:
                return self._build_reject(
                    actor=actor,
                    stages=stages_executed,
                    failed_stage=stage_name,
                    reason="Receipt mismatch: parent_receipt signature is missing or invalid",
                    contradictions=contradictions,
                )

            parent_signing_payload = {
                "parent_task_id": p_task,
                "parent_passport_hash": p_hash,
            }
            if p_sig.startswith(SPEK_SIG_PREFIXES):
                if not self.attestation_provider.verify(parent_signing_payload, p_sig):
                    return self._build_reject(
                        actor=actor,
                        stages=stages_executed,
                        failed_stage=stage_name,
                        reason="Receipt mismatch: parent_receipt cryptographic signature verification failed",
                        contradictions=contradictions,
                    )

        # =====================================================================
        # STAGE 5: Contradiction Detection
        # =====================================================================
        stage_name = "CONTRADICTION_DETECTION"
        stages_executed.append(stage_name)

        nonce = pack_dict.get("nonce")
        if nonce in self.seen_nonces:
            contradictions.append(
                ERIPContradictionFinding(
                    contradiction_type="DUPLICATE_NONCE",
                    description=f"Duplicate nonce '{nonce}' detected across intake stream",
                    affected_boundary="NONCE_REPLAY_PREVENTION",
                )
            )

        # Check timestamp freshness and ordering
        pack_ts_str = pack_dict.get("timestamp")
        try:
            pack_dt = datetime.fromisoformat(pack_ts_str.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            age = (now_dt - pack_dt).total_seconds()

            if age < -60.0:  # Far in future
                contradictions.append(
                    ERIPContradictionFinding(
                        contradiction_type="STALE_EVIDENCE",
                        description=f"Timestamp '{pack_ts_str}' is in the future",
                        affected_boundary="MONOTONIC_SEQUENCE_ENFORCEMENT",
                    )
                )
            elif age > self.max_age_seconds:
                contradictions.append(
                    ERIPContradictionFinding(
                        contradiction_type="STALE_EVIDENCE",
                        description=f"Evidence package age ({age:.1f}s) exceeds maximum threshold ({self.max_age_seconds:.1f}s)",
                        affected_boundary="TIMESTAMP_FRESHNESS",
                    )
                )
        except Exception as e:
            contradictions.append(
                ERIPContradictionFinding(
                    contradiction_type="STALE_EVIDENCE",
                    description=f"Invalid timestamp format '{pack_ts_str}': {str(e)}",
                    affected_boundary="TIMESTAMP_PARSING",
                )
            )

        # Check subtasks vs decision evidence
        subtask_ids = task_lineage.get("subtask_ids", [])
        decision_events = cmaps_payload.get("decision_events", [])
        if subtask_ids and not decision_events:
            contradictions.append(
                ERIPContradictionFinding(
                    contradiction_type="MISSING_RECEIPTS",
                    description=f"Subtasks {subtask_ids} declared but zero decision receipts recorded in CMAPS",
                    affected_boundary="SUBTASK_DECISION_ALIGNMENT",
                )
            )

        # Check historical archive reference if provided
        archive_ref = pack_dict.get("historical_archive_ref")
        if archive_ref:
            target_file = self.root_dir / archive_ref
            if not target_file.exists():
                contradictions.append(
                    ERIPContradictionFinding(
                        contradiction_type="ARCHIVE_DIVERGENCE",
                        description=f"Referenced historical archive file '{archive_ref}' does not exist on disk",
                        affected_boundary="MASTER_ARCHIVE_CONSISTENCY",
                    )
                )

        if contradictions:
            return self._build_reject(
                actor=actor,
                stages=stages_executed,
                failed_stage=stage_name,
                reason=f"Logical contradictions detected: {[c.description for c in contradictions]}",
                contradictions=contradictions,
                integrity_verified=integrity_verified,
            )

        # Record nonce if successful
        if nonce:
            self.seen_nonces.add(nonce)

        # =====================================================================
        # STAGE 6: Deterministic Validation Result
        # =====================================================================
        stage_name = "DETERMINISTIC_RESULT_GENERATION"
        stages_executed.append(stage_name)

        result = ERIPValidationResult(
            actor_identity=actor,
            stages_executed=stages_executed,
            status="PASS",
            failed_stage=None,
            failure_reason=None,
            contradiction_findings=[],
            integrity_root_verified=integrity_verified,
            promoted_to_canonical=False,
        )
        result.provenance_hash = result.compute_provenance_hash()
        return result

    def _build_reject(
        self,
        actor: Dict[str, Any],
        stages: List[str],
        failed_stage: str,
        reason: str,
        contradictions: List[ERIPContradictionFinding],
        integrity_verified: bool = False,
    ) -> ERIPValidationResult:
        """Helper to build a fail-closed rejection result."""
        finding_dicts = [c.model_dump() for c in contradictions]
        result = ERIPValidationResult(
            actor_identity=actor,
            stages_executed=stages,
            status="REJECT",
            failed_stage=failed_stage,
            failure_reason=reason,
            contradiction_findings=finding_dicts,
            integrity_root_verified=integrity_verified,
            promoted_to_canonical=False,
        )
        result.provenance_hash = result.compute_provenance_hash()
        return result
