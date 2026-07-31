"""SAGE-ACT Milestone 5: Cryptographic Session Receipt Chain (SAGE-CRC) Adversarial Tests."""

import pytest
import time
import hashlib
from typing import Dict, Any
from sage.experimental.act.contracts import CryptographicSessionReceiptChain


def test_valid_cryptographic_session_receipt_chain():
    """Verify that a properly constructed sequential chain successfully validates."""
    chain_validator = CryptographicSessionReceiptChain()

    session_id = "session_f1d2c3b4"
    agent_id = "agent_jules"
    p1 = hashlib.sha256(b"payload_1").hexdigest()
    p2 = hashlib.sha256(b"payload_2").hexdigest()
    p3 = hashlib.sha256(b"payload_3").hexdigest()

    # 1. Build genesis block
    genesis = chain_validator.build_genesis_block(session_id, p1, agent_id)
    assert genesis["sequence_number"] == 0
    assert genesis["previous_hash"] == "0" * 64
    assert genesis["signer_identity"] == agent_id

    # 2. Append block 1
    block_1 = chain_validator.append_receipt_block(genesis, p2, agent_id)
    assert block_1["sequence_number"] == 1
    assert block_1["previous_hash"] == genesis["current_hash"]

    # 3. Append block 2
    block_2 = chain_validator.append_receipt_block(block_1, p3, agent_id)
    assert block_2["sequence_number"] == 2
    assert block_2["previous_hash"] == block_1["current_hash"]

    # Verify entire chain
    chain = [genesis, block_1, block_2]
    assert chain_validator.verify_chain_integrity(chain) is True


def test_genesis_invalid_sequence():
    """Genesis block must have sequence_number=0."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a8e2b7c1"
    p1 = hashlib.sha256(b"p1").hexdigest()
    agent_id = "agent_coordinator"

    genesis = chain_validator.build_genesis_block(session_id, p1, agent_id)
    genesis["sequence_number"] = 1  # Corrupt sequence

    # Re-sign to bypass signature verification, forcing it to hit the sequence check
    genesis["signature"] = chain_validator.generate_mock_signature(genesis["current_hash"], agent_id)

    with pytest.raises(ValueError, match="Genesis block must have sequence_number=0"):
        chain_validator.verify_chain_integrity([genesis])


def test_genesis_invalid_previous_hash():
    """Genesis block previous_hash must be sixty-four zeros."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a8e2b7c1"
    p1 = hashlib.sha256(b"p1").hexdigest()
    agent_id = "agent_coordinator"

    genesis = chain_validator.build_genesis_block(session_id, p1, agent_id)
    genesis["previous_hash"] = "f" * 64  # Corrupt previous hash

    # Re-calculate hash and signature to focus on genesis previous hash check
    canonical_bytes = chain_validator.canonicalize_block(genesis)
    genesis["current_hash"] = hashlib.sha256(canonical_bytes).hexdigest()
    genesis["signature"] = chain_validator.generate_mock_signature(genesis["current_hash"], agent_id)

    with pytest.raises(ValueError, match="Genesis block previous_hash must be sixty-four zeros"):
        chain_validator.verify_chain_integrity([genesis])


def test_sequence_gap_detection():
    """Sequence numbers must be consecutive (S_i = S_{i-1} + 1)."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a1b2c3d4"
    agent_id = "agent_jules"

    genesis = chain_validator.build_genesis_block(session_id, hashlib.sha256(b"1").hexdigest(), agent_id)
    block_1 = chain_validator.append_receipt_block(genesis, hashlib.sha256(b"2").hexdigest(), agent_id)

    # Introduce a gap (sequence skip)
    block_2 = chain_validator.append_receipt_block(block_1, hashlib.sha256(b"3").hexdigest(), agent_id)
    block_2["sequence_number"] = 3  # skip sequence 2

    # Re-calculate hash and signature
    canonical_bytes = chain_validator.canonicalize_block(block_2)
    block_2["current_hash"] = hashlib.sha256(canonical_bytes).hexdigest()
    block_2["signature"] = chain_validator.generate_mock_signature(block_2["current_hash"], agent_id)

    chain = [genesis, block_1, block_2]
    with pytest.raises(ValueError, match="Sequence gap at index 2"):
        chain_validator.verify_chain_integrity(chain)


def test_hash_discontinuity_detection():
    """Hash chain discontinuity must be detected and fail closed."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a1b2c3d4"
    agent_id = "agent_jules"

    genesis = chain_validator.build_genesis_block(session_id, hashlib.sha256(b"1").hexdigest(), agent_id)
    block_1 = chain_validator.append_receipt_block(genesis, hashlib.sha256(b"2").hexdigest(), agent_id)

    # Tamper with the linkage between block_1 and block_2
    block_2 = chain_validator.append_receipt_block(block_1, hashlib.sha256(b"3").hexdigest(), agent_id)
    block_2["previous_hash"] = "e" * 64  # Break linkage

    # Re-calculate hash and signature
    canonical_bytes = chain_validator.canonicalize_block(block_2)
    block_2["current_hash"] = hashlib.sha256(canonical_bytes).hexdigest()
    block_2["signature"] = chain_validator.generate_mock_signature(block_2["current_hash"], agent_id)

    chain = [genesis, block_1, block_2]
    with pytest.raises(ValueError, match="Hash discontinuity at index 2"):
        chain_validator.verify_chain_integrity(chain)


def test_temporal_monotonicity_violation():
    """Subsequent block timestamps must be strictly non-decreasing."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a1b2c3d4"
    agent_id = "agent_jules"

    genesis = chain_validator.build_genesis_block(session_id, hashlib.sha256(b"1").hexdigest(), agent_id)
    block_1 = chain_validator.append_receipt_block(genesis, hashlib.sha256(b"2").hexdigest(), agent_id)

    # Backdate block 1 to a future time, or block_2 to an earlier time
    block_2 = chain_validator.append_receipt_block(block_1, hashlib.sha256(b"3").hexdigest(), agent_id)
    block_2["timestamp"] = "2020-01-01T00:00:00Z"  # Backdated timestamp

    # Re-calculate hash and signature
    canonical_bytes = chain_validator.canonicalize_block(block_2)
    block_2["current_hash"] = hashlib.sha256(canonical_bytes).hexdigest()
    block_2["signature"] = chain_validator.generate_mock_signature(block_2["current_hash"], agent_id)

    chain = [genesis, block_1, block_2]
    with pytest.raises(ValueError, match="Chronological violation at index 2"):
        chain_validator.verify_chain_integrity(chain)


def test_signature_forgery_detection():
    """Signature mismatch/forgery must fail validation."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a1b2c3d4"
    agent_id = "agent_jules"

    genesis = chain_validator.build_genesis_block(session_id, hashlib.sha256(b"1").hexdigest(), agent_id)
    genesis["signature"] = "forged_signature_value_here"

    with pytest.raises(ValueError, match="Signature authentication failure at index 0"):
        chain_validator.verify_chain_integrity([genesis])


def test_hash_payload_tampering_detection():
    """Modifying raw block payload parameters without re-signing must fail validation."""
    chain_validator = CryptographicSessionReceiptChain()
    session_id = "session_a1b2c3d4"
    agent_id = "agent_jules"

    genesis = chain_validator.build_genesis_block(session_id, hashlib.sha256(b"1").hexdigest(), agent_id)

    # Direct raw payload tampering without hash recalculation
    genesis["payload_hash"] = "a" * 64

    with pytest.raises(ValueError, match="Hash mismatch at index 0"):
        chain_validator.verify_chain_integrity([genesis])


def test_empty_chain_exception():
    """Verifying an empty chain must throw a ValueError."""
    chain_validator = CryptographicSessionReceiptChain()
    with pytest.raises(ValueError, match="Chain cannot be empty"):
        chain_validator.verify_chain_integrity([])
