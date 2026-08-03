"""Unit test suite for SAGE-CRC-2.0 Asymmetric Cryptographic Receipt Chain Foundation."""

import os
import json
import pytest
from datetime import datetime, timezone
from sage.experimental.act.crc_002_asymmetric import (
    AsymmetricKeyManager,
    AsymmetricReceiptChainGenerator,
    AsymmetricReceiptVerifier,
    AsymmetricEvidenceGenerator
)


def test_asymmetric_key_generation_and_signing():
    """Verify deterministic RSA-like keypair generation, signing, and verification."""
    km = AsymmetricKeyManager()

    # Deterministic generation for individual agent personas
    coord_keys = km.generate_agent_keypair("agent_coord_01")
    exec_keys = km.generate_agent_keypair("agent_exec_01")

    assert coord_keys["agent_id"] == "agent_coord_01"
    assert exec_keys["agent_id"] == "agent_exec_01"

    # Keys must be distinct
    assert coord_keys["private_key"]["d"] != exec_keys["private_key"]["d"]
    assert coord_keys["public_key"]["e"] != exec_keys["public_key"]["e"]

    # Basic signature sanity
    msg = "SAGE-CRC-2.0 verification challenge"
    sig = km.sign_message(msg, coord_keys["private_key"])

    # Correct signature verifies successfully
    assert km.verify_signature(msg, sig, coord_keys["public_key"]) is True

    # Verifying with the wrong public key must fail (Asymmetric properties)
    assert km.verify_signature(msg, sig, exec_keys["public_key"]) is False

    # Verifying with a tampered message must fail
    assert km.verify_signature(msg + " tampered", sig, coord_keys["public_key"]) is False

    # Verifying with a bad signature string format must fail gracefully
    assert km.verify_signature(msg, "invalid_hex_string", coord_keys["public_key"]) is False


def test_asymmetric_receipt_chaining_and_purity():
    """Verify successful formulation, sequence validation, and verification of receipt chains."""
    km = AsymmetricKeyManager()
    coord_keys = km.generate_agent_keypair("agent_coord_01")
    exec_keys = km.generate_agent_keypair("agent_exec_01")

    generator = AsymmetricReceiptChainGenerator("session_crc2_01", km)

    # Enforce session id contract
    with pytest.raises(ValueError, match="Invalid session_id"):
        AsymmetricReceiptChainGenerator("invalid_id", km)

    # Enforce task id contract
    with pytest.raises(ValueError, match="Invalid task_id"):
        generator.append_signed_receipt(
            "invalid_task", "obj_audit", "agent_coord_01", coord_keys["private_key"], coord_keys["public_key"], {}
        )

    # Append first signed receipt
    r1 = generator.append_signed_receipt(
        "task_init", "obj_audit", "agent_coord_01", coord_keys["private_key"], coord_keys["public_key"], {"status": "started"}
    )
    assert r1["node_content"]["prev_hash"] == generator.genesis_hash

    # Append second signed receipt linked to the first
    r2 = generator.append_signed_receipt(
        "task_exec", "obj_audit", "agent_exec_01", exec_keys["private_key"], exec_keys["public_key"], {"status": "success"}
    )
    assert r2["node_content"]["prev_hash"] == r1["receipt_hash"]

    # Run verifier over pristine chain
    verifier = AsymmetricReceiptVerifier(km)
    report = verifier.verify_chain(generator.receipts)

    assert report["status"] == "PASSED"
    assert report["receipts_checked"] == 2
    assert len(report["errors"]) == 0


def test_forgery_and_sequence_mutation_detection():
    """Verify that verifier catches forged signatures, modified payloads, and sequence breaks."""
    km = AsymmetricKeyManager()
    coord_keys = km.generate_agent_keypair("agent_coord_01")
    exec_keys = km.generate_agent_keypair("agent_exec_01")

    generator = AsymmetricReceiptChainGenerator("session_crc2_02", km)
    r1 = generator.append_signed_receipt(
        "task_init", "obj_audit", "agent_coord_01", coord_keys["private_key"], coord_keys["public_key"], {"step": 1}
    )
    r2 = generator.append_signed_receipt(
        "task_exec", "obj_audit", "agent_exec_01", exec_keys["private_key"], exec_keys["public_key"], {"step": 2}
    )

    verifier = AsymmetricReceiptVerifier(km)

    # 1. Test Forgery / Parameter Mutation (Alter task metadata)
    r1_tampered = json.loads(json.dumps(generator.receipts))
    r1_tampered[0]["node_content"]["payload_data"]["step"] = 99  # Tamper payload

    report_tampered = verifier.verify_chain(r1_tampered)
    assert report_tampered["status"] == "FAILED"
    assert any("invalid signature" in err for err in report_tampered["errors"])

    # 2. Test Chronological Sequence Break (Inject task out-of-order)
    r_broken = json.loads(json.dumps(generator.receipts))
    r_broken[1]["node_content"]["prev_hash"] = "broken_hash_000000"  # Inject sequence error

    report_broken = verifier.verify_chain(r_broken)
    assert report_broken["status"] == "FAILED"
    assert any("breaks chronological chain" in err for err in report_broken["errors"])


def test_asymmetric_evidence_generation(tmp_path):
    """Verify standard compliant SAGE-CRC-2.0 evidence serialization and vocabulary rules."""
    km = AsymmetricKeyManager()
    coord_keys = km.generate_agent_keypair("agent_coord_01")

    generator = AsymmetricReceiptChainGenerator("session_crc2_03", km)
    generator.append_signed_receipt(
        "task_init", "obj_audit", "agent_coord_01", coord_keys["private_key"], coord_keys["public_key"], {"init": True}
    )

    verifier = AsymmetricReceiptVerifier(km)
    report = verifier.verify_chain(generator.receipts)

    evidence_file = tmp_path / "crc_002_asymmetric_evidence.json"
    ev_generator = AsymmetricEvidenceGenerator(output_path=str(evidence_file))

    evidence_pack = ev_generator.write_evidence("session_crc2_03", generator.receipts, report)

    # Check structural compliance
    assert "asymmetric_session_id" in evidence_pack
    assert "timestamp" in evidence_pack
    assert "asymmetric_participants" in evidence_pack
    assert "receipt_lineage" in evidence_pack
    assert "verification_report" in evidence_pack
    assert "observed_results" in evidence_pack
    assert "boundary_integrity_verification" in evidence_pack

    # Non-absolute language verification
    observed = evidence_pack["observed_results"]
    assert "total_receipts_compiled" in observed
    assert "cryptographic_verification_speed_secs" in observed
    assert "estimated_baseline_forgery_resistance_percent" in observed

    # Check safe persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["asymmetric_session_id"] == "session_crc2_03"
    assert loaded["boundary_integrity_verification"]["sage_runtime_untouched"] is True
