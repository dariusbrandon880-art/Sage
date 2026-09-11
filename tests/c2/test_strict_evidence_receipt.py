import pytest

from sage.c2.evidence.receipt_schema import ProvenanceTuple, StrictEvidenceReceipt


def test_strict_evidence_receipt_validation_and_verification():
    sha1 = "fc768ee91d0d8ee8c153a1bd647f3b784dbccf1c"
    sha2 = "1992544bb333451ece53621717767fae190ce9f2"
    artifact_digest = "sha256:" + "a" * 64

    provenance = ProvenanceTuple(
        wave_id="wave-001",
        flight_id="F1",
        executed_head=sha1,
        base_commit=sha2,
        workflow_run_id="run-100",
        job_id="job-100",
        artifact_digest=artifact_digest,
    )

    provenance.validate()
    assert provenance.as_dict()["wave_id"] == "wave-001"

    receipt = StrictEvidenceReceipt(
        receipt_id="rcpt-001",
        provenance=provenance,
        passed=True,
        metrics={"coverage": 0.98},
    )

    receipt.validate()
    assert receipt.receipt_digest().startswith("sha256:")
    assert receipt.verify_against_context(provenance, artifact_digest) is True


def test_strict_evidence_receipt_fails_closed_on_invalid_sha():
    provenance = ProvenanceTuple(
        wave_id="wave-001",
        flight_id="F1",
        executed_head="invalid-sha",
        base_commit="invalid-sha",
        workflow_run_id="run-100",
        job_id="job-100",
        artifact_digest="sha256:" + "a" * 64,
    )
    with pytest.raises(ValueError, match="commit SHA"):
        provenance.validate()
