"""Adversarial test suite for SAGE C2 Live Operation Receipt Source Provenance & Attestation."""

import json
import hashlib
from datetime import datetime, timezone
import pytest

from sage.c2.live_operation_receipt import (
    LiveOperationReceipt,
    execute_live_capability,
    persist_live_operation_receipt,
    rehydrate_live_operation_receipt,
)
from sage.acr.attestation import AttestationProvider


class DummyLiveCapability:
    capability_id = "test-live-cap"

    def invoke(self, *, operation: str, task: str):
        return {
            "target_resource": "dariusbrandon880-art/Sage",
            "success": True,
            "result": {"status": "ok", "task": task}
        }


def test_valid_operation_boundary_receipt_creation_and_verification():
    cap = DummyLiveCapability()
    receipt = execute_live_capability(cap, operation="inspect_pr", task="PR #251")
    assert receipt.verify() is True
    assert receipt.source_id == "sage-c2-operation-boundary"
    assert receipt.source_signature.startswith("mock_attestation_")


def test_caller_forged_receipt_without_signature_fails_verification():
    ts = datetime.now(timezone.utc).isoformat()
    digest = "a" * 64
    payload = {
        "operation": "inspect_pr",
        "capability": "test-cap",
        "target_resource": "repo",
        "timestamp": ts,
        "success": True,
        "result_digest": digest,
        "source_id": "caller-fake-source",
    }
    receipt_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    forged_receipt = LiveOperationReceipt(
        operation="inspect_pr",
        capability="test-cap",
        target_resource="repo",
        timestamp=ts,
        success=True,
        result_digest=digest,
        receipt_hash=receipt_hash,
        source_id="caller-fake-source",
        source_signature=""  # Unsigned
    )

    assert forged_receipt.verify() is False


def test_caller_forged_signature_fails_verification():
    ts = datetime.now(timezone.utc).isoformat()
    digest = "b" * 64
    payload = {
        "operation": "inspect_pr",
        "capability": "test-cap",
        "target_resource": "repo",
        "timestamp": ts,
        "success": True,
        "result_digest": digest,
        "source_id": "caller-fake-source",
    }
    receipt_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    forged_receipt = LiveOperationReceipt(
        operation="inspect_pr",
        capability="test-cap",
        target_resource="repo",
        timestamp=ts,
        success=True,
        result_digest=digest,
        receipt_hash=receipt_hash,
        source_id="caller-fake-source",
        source_signature="mock_attestation_invalidfakesignature12345"
    )

    assert forged_receipt.verify() is False


def test_persistence_and_rehydration_provenance(tmp_path):
    cap = DummyLiveCapability()
    receipt = execute_live_capability(cap, operation="check_repo", task="verify")
    receipt_path = tmp_path / "valid_receipt.json"

    persist_live_operation_receipt(receipt, receipt_path)
    rehydrated = rehydrate_live_operation_receipt(receipt_path)

    assert rehydrated.verify() is True
    assert rehydrated.receipt_hash == receipt.receipt_hash


def test_rehydrating_tampered_payload_fails_closed(tmp_path):
    cap = DummyLiveCapability()
    receipt = execute_live_capability(cap, operation="check_repo", task="verify")
    receipt_path = tmp_path / "tampered_receipt.json"

    persist_live_operation_receipt(receipt, receipt_path)

    # Tamper payload on disk
    raw_data = json.loads(receipt_path.read_text(encoding="utf-8"))
    raw_data["target_resource"] = "tampered/repo"
    receipt_path.write_text(json.dumps(raw_data), encoding="utf-8")

    with pytest.raises(ValueError, match="failed replay verification or source signature check"):
        rehydrate_live_operation_receipt(receipt_path)
