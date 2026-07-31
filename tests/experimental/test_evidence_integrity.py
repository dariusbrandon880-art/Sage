"""SAGE-ACT Evidence Integrity Verification Validation Tests."""

import pytest
import os
import json
import tempfile
from typing import Dict, Any
from sage.experimental.act.integrity import EvidenceIntegrityVerifier


def test_evidence_integrity_valid_file_checks():
    """Verify that existing active evidence files pass validation."""
    verifier = EvidenceIntegrityVerifier()
    results = verifier.audit_evidence_chain()

    # Checks the status of sdr_crc_evidence_package.json
    crc_path = "evidence_capture/sdr_crc_evidence_package.json"
    assert crc_path in results
    assert results[crc_path]["status"] == "VALID"
    assert results[crc_path]["required_fields_present"] is True
    assert results[crc_path]["validation_error"] is None

    # Checks the status of sdr_gal_evidence_package.json
    gal_path = "evidence_capture/sdr_gal_evidence_package.json"
    assert gal_path in results
    assert results[gal_path]["status"] == "VALID"
    assert results[gal_path]["required_fields_present"] is True

    # Check overall non-strict integrity report passes
    report = verifier.generate_integrity_report(strict_mode=False)
    assert report["validation_outcome"] == "PASSED"
    assert report["human_review_status"] == "APPROVED_BY_HUMAN_SUPERVISOR"


def test_evidence_integrity_missing_artifact_detection():
    """Verify that missing files report status as MISSING, and block strict-mode reports."""
    verifier = EvidenceIntegrityVerifier()
    results = verifier.audit_evidence_chain()

    missing_path = "evidence_capture/sdr_exp_001_evidence_package.json"
    assert missing_path in results
    assert results[missing_path]["status"] == "MISSING"
    assert results[missing_path]["required_fields_present"] is False

    # Under strict_mode=True, a missing file triggers fail-closed exception
    with pytest.raises(ValueError, match="Strict Mode Block: Missing artifact"):
        verifier.generate_integrity_report(strict_mode=True)


def test_evidence_integrity_modified_schema_rejection_fail_closed():
    """Verify that tampering with a file schema is detected and triggers fail-closed behavior."""
    # Create a temporary workspace to simulate a corrupted file
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "evidence_capture"), exist_ok=True)

        # Write valid mock files
        valid_crc = {"experiment_id": "test_crc", "blocks": [], "verification": {}}
        valid_gal = {"gal_run_id": "test_gal", "changed_files": [], "boundary_status": {}, "test_results": {}}

        with open(os.path.join(tmp_dir, "evidence_capture/sdr_crc_evidence_package.json"), "w") as f:
            json.dump(valid_crc, f)

        # Tampered GAL file (missing required 'test_results' field)
        tampered_gal = {"gal_run_id": "test_gal", "changed_files": [], "boundary_status": {}}
        with open(os.path.join(tmp_dir, "evidence_capture/sdr_gal_evidence_package.json"), "w") as f:
            json.dump(tampered_gal, f)

        verifier = EvidenceIntegrityVerifier(workspace_root=tmp_dir)
        results = verifier.audit_evidence_chain()

        gal_path = "evidence_capture/sdr_gal_evidence_package.json"
        assert results[gal_path]["status"] == "INVALID_SCHEMA"
        assert results[gal_path]["required_fields_present"] is False
        assert "Missing required schema fields" in results[gal_path]["validation_error"]

        # Ensure calling generate_integrity_report fails closed even under non-strict mode
        with pytest.raises(ValueError, match="failed integrity validation"):
            verifier.generate_integrity_report(strict_mode=False)


def test_evidence_integrity_corrupted_json_detection():
    """Verify that malformed/corrupted JSON triggers a CORRUPTED_JSON status and fails validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "evidence_capture"), exist_ok=True)

        # Write malformed JSON
        with open(os.path.join(tmp_dir, "evidence_capture/sdr_crc_evidence_package.json"), "w") as f:
            f.write("{invalid_json_formatting_here]")

        verifier = EvidenceIntegrityVerifier(workspace_root=tmp_dir)
        results = verifier.audit_evidence_chain()

        crc_path = "evidence_capture/sdr_crc_evidence_package.json"
        assert results[crc_path]["status"] == "CORRUPTED_JSON"
        assert "JSON Decode Error" in results[crc_path]["validation_error"]

        with pytest.raises(ValueError, match="failed integrity validation"):
            verifier.generate_integrity_report(strict_mode=False)
