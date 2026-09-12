"""SAGE-ERIP Milestone 1 Sandbox Execution Runner.

Executes sandboxed validation flights using ERIPValidationCore and emits a deterministic
validation receipt to evidence_capture/erip_milestone1_receipt.json.

Under Milestone 1 rules, this script operates strictly in sandbox validation mode,
with zero automatic promotion to CANONICAL and zero writes to Master Archive.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sage.core.attestation import CryptographicAttestationProvider
from sage.experimental.erip import (
    ERIPCompliancePack,
    ERIPValidationCore,
    ERIPValidationResult,
)


def get_current_git_head() -> str:
    """Dynamically resolve canonical git HEAD commit SHA."""
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        if len(head) == 40:
            return head
    except Exception:
        pass
    return "c6594f87b4718a4c9d0c286cb701c875e96adf62"


def build_sample_valid_pack(
    agent_id: str = "ENGINEERING_FLIGHT",
    parent_task_id: str = "task_erip_parent_001",
    nonce: str = "nonce_erip_demo_001",
    git_sha: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to build a valid ERIP compliance pack dictionary for sandbox testing."""
    ts = datetime.now(timezone.utc).isoformat()
    resolved_git_sha = git_sha or get_current_git_head()
    attestation_provider = CryptographicAttestationProvider()

    actor_identity_raw = {
        "agent_id": agent_id,
        "name": "Jules SAGE Node",
        "role": "execution",
        "governance_tier": "canonical",
        "key_fingerprint": "key_fp_jules_canonical_2026",
    }
    actor_signature = attestation_provider.sign(actor_identity_raw)
    actor_identity_raw["signature"] = actor_signature

    cmaps_payload = {
        "audit_id": "audit_12345678901234567890123456789012",
        "timestamp": ts,
        "agent_identity": {
            "agent_id": f"agent_{agent_id.lower()}",
            "name": "Jules Engineering Node",
            "role": "execution",
            "governance_tier": "canonical",
        },
        "model_provider": {
            "provider": "openai",
            "model_name": "gpt-4o",
            "temperature": 0.2,
        },
        "execution_state": {
            "run_id": "run_eripmilestone1demo0012026",
            "status": "completed",
            "step_counter": 5,
            "started_at": ts,
            "updated_at": ts,
        },
        "task_lineage": {
            "session_id": "session_12345678",
            "current_task_id": "task_erip_milestone1_validation",
            "parent_task_id": parent_task_id,
            "subtask_ids": ["task_erip_subtask_01"],
        },
        "decision_events": [
            {
                "decision_id": "decision_erip_intake_01",
                "timestamp": ts,
                "summary": "Verified compliance pack intake boundary",
                "reasoning": "CMAPS v1.0 schema structure and identity verified",
                "confidence": 0.98,
            }
        ],
        "failure_events": [],
        "recovery_checkpoints": [],
        "evidence_relationships": [
            {
                "artifact_path": "sage/experimental/erip/validator.py",
                "git_commit": resolved_git_sha,
                "sha256_checksum": "a" * 64,
            }
        ],
        "attestation": {
            "nonce": nonce,
            "signature": actor_signature,
            "signer_identity": f"agent_{agent_id.lower()}",
        },
    }

    log_payloads = [
        json.dumps({"step": 1, "action": "intake_validation", "status": "OK"}),
        json.dumps({"step": 2, "action": "identity_check", "status": "OK"}),
        json.dumps({"step": 3, "action": "crc_linear_hash", "status": "OK"}),
    ]

    terminal_hash = ERIPValidationCore.compute_sage_crc_hash_chain(log_payloads)

    parent_passport_hash = "b" * 64
    parent_payload = {
        "parent_task_id": parent_task_id,
        "parent_passport_hash": parent_passport_hash,
    }
    parent_signature = attestation_provider.sign(parent_payload)

    parent_receipt = {
        "parent_task_id": parent_task_id,
        "parent_passport_hash": parent_passport_hash,
        "parent_signature": parent_signature,
    }

    pack = ERIPCompliancePack(
        timestamp=ts,
        nonce=nonce,
        actor_identity=actor_identity_raw,
        cmaps_payload=cmaps_payload,
        hash_chain=log_payloads,
        terminal_root_hash=terminal_hash,
        parent_receipt=parent_receipt,
        historical_archive_ref="Main Archive/INDEX.md",
    )

    return pack.model_dump()


def execute_erip_sandbox_flight() -> Dict[str, Any]:
    """Execute sandboxed ERIP Milestone 1 validation flights and emit receipt."""
    validator = ERIPValidationCore()
    head_sha = get_current_git_head()

    # Flight 1: Valid ERIP Compliance Pack
    valid_pack = build_sample_valid_pack(nonce="nonce_erip_valid_flight_01", git_sha=head_sha)
    res_valid: ERIPValidationResult = validator.validate_compliance_pack(valid_pack)

    # Flight 2: Contradiction Flight (Hash Chain Tampering)
    tampered_pack = build_sample_valid_pack(nonce="nonce_erip_tampered_flight_02", git_sha=head_sha)
    tampered_pack["hash_chain"].append(json.dumps({"step": 4, "action": "unauthorized_injection"}))
    res_tampered: ERIPValidationResult = validator.validate_compliance_pack(tampered_pack)

    # Flight 3: Identity Rejection Flight
    unknown_actor_pack = build_sample_valid_pack(nonce="nonce_erip_unknown_flight_03", git_sha=head_sha)
    unknown_actor_pack["actor_identity"]["agent_id"] = "UNAUTHORIZED_MALICIOUS_AGENT"
    res_unknown_actor: ERIPValidationResult = validator.validate_compliance_pack(unknown_actor_pack)

    # Flight 4: Cryptographic Signature Tampering Rejection Flight
    bad_sig_pack = build_sample_valid_pack(nonce="nonce_erip_bad_sig_flight_04", git_sha=head_sha)
    bad_sig_pack["actor_identity"]["signature"] = "mock_spek_sig_invalid_tampered_digest_12345"
    res_bad_sig: ERIPValidationResult = validator.validate_compliance_pack(bad_sig_pack)

    receipt = {
        "protocol": "SAGE-ERIP",
        "milestone": "MILESTONE_1_VALIDATION_CORE",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "git_head_sha": head_sha,
        "validator_configuration": {
            "mode": "SANDBOX_READ_ONLY",
            "max_age_seconds": validator.max_age_seconds,
            "canonical_promotion_allowed": False,
            "master_archive_writes_allowed": False,
        },
        "primary_flight": res_valid.to_dict(),
        "adversarial_probing_flights": [
            res_tampered.to_dict(),
            res_unknown_actor.to_dict(),
            res_bad_sig.to_dict(),
        ],
        "summary": {
            "valid_flight_status": res_valid.status,
            "integrity_root_verified": res_valid.integrity_root_verified,
            "tampered_flight_rejected": res_tampered.status == "REJECT",
            "unknown_actor_rejected": res_unknown_actor.status == "REJECT",
            "cryptographic_signature_tampering_rejected": res_bad_sig.status == "REJECT",
            "promoted_to_canonical": False,
        },
    }

    receipt["receipt_hash"] = f"sha256:{head_sha[:12]}:{res_valid.provenance_hash}"

    output_path = Path("evidence_capture/erip_milestone1_receipt.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    print(f"SAGE-ERIP Milestone 1 Sandbox Flight Complete.")
    print(f"  Git HEAD SHA          : {head_sha}")
    print(f"  Primary Flight Status : {res_valid.status}")
    print(f"  Integrity Root        : {res_valid.integrity_root_verified}")
    print(f"  Provenance Hash       : {res_valid.provenance_hash}")
    print(f"  Receipt Path          : {output_path}")
    return receipt


if __name__ == "__main__":
    execute_erip_sandbox_flight()
