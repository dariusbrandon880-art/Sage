"""Tests for the SAGE Local Integrity evidence boundary."""

import hashlib

import pytest

from sage.c2.evidence import (
    AggregatorError,
    ImmutableEvidenceRegistry,
    ProvenanceTuple,
    ReconvergenceAggregator,
    StrictEvidenceReceipt,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


def provenance(front: str, digest: str = "sha256:" + "1" * 64) -> ProvenanceTuple:
    return ProvenanceTuple(
        wave_id="wave-001",
        flight_id=front,
        executed_head=SHA_A,
        base_commit=SHA_B,
        workflow_run_id="run-123",
        job_id=f"job-{front}",
        artifact_digest=digest,
    )


def receipt(front: str) -> StrictEvidenceReceipt:
    p = provenance(front)
    return StrictEvidenceReceipt(
        receipt_id=f"receipt-{front}",
        provenance=p,
        passed=True,
    )


def test_receipt_requires_exact_provenance_and_independent_digest():
    p = provenance("F1")
    r = receipt("F1")
    observed = p.artifact_digest
    assert r.verify_against_context(p, observed)
    assert not r.verify_against_context(provenance("F1", "sha256:" + "2" * 64), observed)
    assert not r.verify_against_context(p, "sha256:" + "2" * 64)


def test_receipt_rejects_malformed_artifact_digest():
    with pytest.raises(ValueError):
        provenance("F1", "not-a-digest").validate()


def test_aggregator_fails_closed_on_missing_front():
    aggregator = ReconvergenceAggregator()
    expected = {f"F{i}": provenance(f"F{i}") for i in range(1, 6)}
    receipts = {f"F{i}": receipt(f"F{i}") for i in range(1, 5)}
    digests = {front: expected[front].artifact_digest for front in receipts}
    with pytest.raises(AggregatorError, match="MISSING_FRONT:F5"):
        aggregator.aggregate_wave("wave-001", expected, receipts, digests)


def test_aggregator_rejects_stale_run_or_job():
    aggregator = ReconvergenceAggregator()
    expected = {f"F{i}": provenance(f"F{i}") for i in range(1, 6)}
    receipts = {f"F{i}": receipt(f"F{i}") for i in range(1, 6)}
    receipts["F3"] = StrictEvidenceReceipt(
        receipt_id="receipt-F3",
        provenance=ProvenanceTuple(
            wave_id="wave-001",
            flight_id="F3",
            executed_head=SHA_A,
            base_commit=SHA_B,
            workflow_run_id="different-run",
            job_id="job-F3",
            artifact_digest="sha256:" + "1" * 64,
        ),
        passed=True,
    )
    digests = {front: expected[front].artifact_digest for front in expected}
    with pytest.raises(AggregatorError, match="INVALID_RECEIPT:F3"):
        aggregator.aggregate_wave("wave-001", expected, receipts, digests)


def test_registry_is_append_only(tmp_path):
    registry = ImmutableEvidenceRegistry(str(tmp_path))
    r = receipt("F1")
    path = registry.register_receipt(r)
    assert path.exists()
    with pytest.raises(FileExistsError, match="IMMUTABLE_RECEIPT_EXISTS"):
        registry.register_receipt(r)


def test_registry_path_contains_execution_identity(tmp_path):
    registry = ImmutableEvidenceRegistry(str(tmp_path))
    path = registry.register_receipt(receipt("F2"))
    assert "waves/wave-001/" in str(path)
    assert path.name == "F2_receipt.json"
