"""Unit tests for SAGE Release Provenance & Attestation Synthesizer."""
import pytest
from sage.c2.release_provenance import (
    ReleaseProvenanceSynthesizer,
    ReleaseProvenanceReceipt,
)
from sage.acr.attestation import AttestationProvider


def test_release_provenance_receipt_digest():
    """Verify ReleaseProvenanceReceipt computes a valid deterministic SHA-256 digest."""
    receipt = ReleaseProvenanceReceipt(
        release_id="rel-2026-v0.1.0",
        commit_sha="af4370abf5270bfdfec962da65ce4bcb40f575a8",
        pyproject_version="0.1.0",
        dependency_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        evidence_refs=["evidence_capture/test.json"],
        attestation_signature="mock_attestation_signature",
    )
    digest = receipt.digest()
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_synthesizer_creates_and_verifies_signed_receipt(tmp_path):
    """Verify ReleaseProvenanceSynthesizer calculates dependency digests and verifies signatures."""
    # Mock pyproject.toml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('version = "0.1.0"\n', encoding="utf-8")

    provider = AttestationProvider(provider_type="Mock", key_seed="test_seed_2026")
    synthesizer = ReleaseProvenanceSynthesizer(root_dir=tmp_path, attestation_provider=provider)

    receipt = synthesizer.synthesize_release_provenance(
        release_id="rel-test-001",
        evidence_refs=["evidence_capture/multi_frontier_dispatch_evidence.json"],
        commit_sha="commit_sha_mock",
    )

    assert receipt.release_id == "rel-test-001"
    assert receipt.commit_sha == "commit_sha_mock"
    assert receipt.pyproject_version == "0.1.0"
    assert receipt.evidence_refs == ["evidence_capture/multi_frontier_dispatch_evidence.json"]
    assert receipt.attestation_signature.startswith("mock_attestation_")

    # Cryptographic verification via AttestationProvider
    payload_signed = {
        "release_id": receipt.release_id,
        "commit_sha": receipt.commit_sha,
        "pyproject_version": receipt.pyproject_version,
        "dependency_digest": receipt.dependency_digest,
        "evidence_refs": receipt.evidence_refs,
    }
    assert provider.verify_signature(payload_signed, receipt.attestation_signature) is True


def test_empty_release_id_raises_value_error():
    """Verify that an empty release_id raises ValueError."""
    synthesizer = ReleaseProvenanceSynthesizer()
    with pytest.raises(ValueError, match="release_id is required"):
        synthesizer.synthesize_release_provenance("   ")
