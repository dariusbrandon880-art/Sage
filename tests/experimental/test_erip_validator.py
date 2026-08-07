"""Unit test suite for SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) Validator."""

import json
import pytest
from sage.experimental.act.erip_validator import SAGEERIPValidator


def test_erip_validator_valid_package():
    """Verify that the ERIP validator successfully reconciles a fully compliant signed package."""
    validator = SAGEERIPValidator()

    # Create linear block chain payload & hashes
    p1 = {"nonce": "nonce_01", "task_id": "task_01", "data": "initialization"}
    h1 = validator.generate_sha256("0" * 64, p1)

    p2 = {"nonce": "nonce_02", "task_id": "task_02", "parent_task_id": "task_01", "data": "processing"}
    h2 = validator.generate_sha256(h1, p2)

    package = {
        "package_id": "pkg_01",
        "session_id": "session_12345678",
        "agent_identity": {
            "agent_id": "agent_jules_sage",
            "governance_tier": "TIER_1_COORDINATOR"
        },
        "trace_blocks": [
            {
                "block_id": "blk_01",
                "payload": p1,
                "block_hash": h1,
                "signed": True
            },
            {
                "block_id": "blk_02",
                "payload": p2,
                "block_hash": h2,
                "signed": True
            }
        ],
        "attestation": {
            "signature": "sig_valid_1234",
            "signer_identity": "supervisor_jules"
        }
    }

    result = validator.validate_ingestion_package(package)

    assert result["validation_status"] == "RECONCILED"
    assert result["evidence_quality_score"] == 1.0
    assert result["total_blocks_verified"] == 2
    assert result["chain_root_hash"] == h2


def test_erip_validator_broken_hash_chain():
    """Verify that the ERIP validator rejects a package with a broken/tampered hash chain."""
    validator = SAGEERIPValidator()

    # Create linear block chain
    p1 = {"nonce": "nonce_01", "task_id": "task_01", "data": "initialization"}
    h1 = validator.generate_sha256("0" * 64, p1)

    p2 = {"nonce": "nonce_02", "task_id": "task_02", "data": "processing"}
    h2 = "f" * 64  # Broken/incorrect hash value

    package = {
        "package_id": "pkg_02",
        "session_id": "session_12345678",
        "agent_identity": {
            "agent_id": "agent_jules_sage",
            "governance_tier": "TIER_1_COORDINATOR"
        },
        "trace_blocks": [
            {
                "block_id": "blk_01",
                "payload": p1,
                "block_hash": h1,
                "signed": True
            },
            {
                "block_id": "blk_02",
                "payload": p2,
                "block_hash": h2,
                "signed": True
            }
        ],
        "attestation": {
            "signature": "sig_valid_1234",
            "signer_identity": "supervisor_jules"
        }
    }

    with pytest.raises(ValueError, match="SAGE-CRC Hash-Chain broken"):
        validator.validate_ingestion_package(package)


def test_erip_validator_relational_contradiction():
    """Verify that the ERIP validator rejects a package with relational/circular cycle loop contradictions."""
    validator = SAGEERIPValidator()

    # Cyclic task parenting (task pointing to itself)
    p1 = {"nonce": "nonce_01", "task_id": "task_circular", "parent_task_id": "task_circular"}
    h1 = validator.generate_sha256("0" * 64, p1)

    package = {
        "package_id": "pkg_03",
        "session_id": "session_12345678",
        "agent_identity": {
            "agent_id": "agent_jules_sage",
            "governance_tier": "TIER_1_COORDINATOR"
        },
        "trace_blocks": [
            {
                "block_id": "blk_01",
                "payload": p1,
                "block_hash": h1,
                "signed": True
            }
        ],
        "attestation": {
            "signature": "sig_valid_1234",
            "signer_identity": "supervisor_jules"
        }
    }

    with pytest.raises(ValueError, match="Relational contradiction detected"):
        validator.validate_ingestion_package(package)


def test_erip_validator_duplicate_nonce_replay():
    """Verify that the ERIP validator rejects duplicated transactional nonces to prevent replay attacks."""
    validator = SAGEERIPValidator()

    # Duplicate nonces across different blocks
    p1 = {"nonce": "nonce_replay_123", "task_id": "task_01"}
    h1 = validator.generate_sha256("0" * 64, p1)

    p2 = {"nonce": "nonce_replay_123", "task_id": "task_02"}
    h2 = validator.generate_sha256(h1, p2)

    package = {
        "package_id": "pkg_04",
        "session_id": "session_12345678",
        "agent_identity": {
            "agent_id": "agent_jules_sage",
            "governance_tier": "TIER_1_COORDINATOR"
        },
        "trace_blocks": [
            {
                "block_id": "blk_01",
                "payload": p1,
                "block_hash": h1,
                "signed": True
            },
            {
                "block_id": "blk_02",
                "payload": p2,
                "block_hash": h2,
                "signed": True
            }
        ],
        "attestation": {
            "signature": "sig_valid_1234",
            "signer_identity": "supervisor_jules"
        }
    }

    with pytest.raises(ValueError, match="Duplicate/Replayed nonce detected"):
        validator.validate_ingestion_package(package)


def test_erip_validator_incomplete_eqs():
    """Verify that the ERIP validator rejects packages with an EQS lower than 1.0 (some blocks unsigned)."""
    validator = SAGEERIPValidator()

    p1 = {"nonce": "nonce_01", "task_id": "task_01"}
    h1 = validator.generate_sha256("0" * 64, p1)

    package = {
        "package_id": "pkg_05",
        "session_id": "session_12345678",
        "agent_identity": {
            "agent_id": "agent_jules_sage",
            "governance_tier": "TIER_1_COORDINATOR"
        },
        "trace_blocks": [
            {
                "block_id": "blk_01",
                "payload": p1,
                "block_hash": h1,
                "signed": False  # Block is unsigned, making EQS < 1.0
            }
        ],
        "attestation": {
            "signature": "sig_valid_1234",
            "signer_identity": "supervisor_jules"
        }
    }

    with pytest.raises(ValueError, match="Evidence Quality Score \\(EQS\\) must equal 1.0"):
        validator.validate_ingestion_package(package)
