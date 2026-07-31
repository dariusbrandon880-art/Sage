"""SAGE Experimental Evidence Integrity Validation Tests."""

import tempfile
import pytest
from pathlib import Path
from sage.experimental.act import EvidenceIntegrityVerifier


def test_manifest_generation_and_success_verification():
    """Verify that EvidenceIntegrityVerifier generates and validates manifests successfully."""
    verifier = EvidenceIntegrityVerifier()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "evidence1.json"
        file2 = tmp_path / "evidence2.json"

        file1.write_text('{"status": "PASSED"}', encoding="utf-8")
        file2.write_text('{"status": "APPROVED"}', encoding="utf-8")

        # Generate manifest
        manifest = verifier.generate_manifest([file1, file2])
        assert manifest["validation_status"] == "INTEGRITY_VERIFIED"
        assert str(file1) in manifest["integrity_results"]
        assert str(file2) in manifest["integrity_results"]

        # Verify manifest
        result = verifier.verify_manifest(manifest)
        assert result["status"] == "SUCCESS"
        assert not result["mismatches"]
        assert not result["missing"]


def test_modified_evidence_detection():
    """Verify that any modification to checked files triggers fail-closed rejection."""
    verifier = EvidenceIntegrityVerifier()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "evidence_tamper.json"
        file1.write_text('{"data": "pristine"}', encoding="utf-8")

        # Generate pristine manifest
        manifest = verifier.generate_manifest([file1])

        # Tamper with file
        file1.write_text('{"data": "tampered"}', encoding="utf-8")

        # Verification must fail and log mismatch
        result = verifier.verify_manifest(manifest)
        assert result["status"] == "FAIL_CLOSED"
        assert len(result["mismatches"]) == 1
        assert result["mismatches"][0]["file"] == str(file1)


def test_missing_evidence_detection():
    """Verify that any missing or deleted file triggers fail-closed rejection."""
    verifier = EvidenceIntegrityVerifier()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "evidence_delete.json"
        file1.write_text('{"data": "delete_me"}', encoding="utf-8")

        # Generate manifest
        manifest = verifier.generate_manifest([file1])

        # Delete file
        file1.unlink()

        # Verification must fail and log missing file
        result = verifier.verify_manifest(manifest)
        assert result["status"] == "FAIL_CLOSED"
        assert str(file1) in result["missing"]
