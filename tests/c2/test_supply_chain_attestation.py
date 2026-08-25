"""Test suite for SAGE C2 Supply Chain Attestation Fabric."""

import pytest
from sage.c2.supply_chain_attestation import SupplyChainAttestationFabric


def test_sbom_generation():
    fabric = SupplyChainAttestationFabric()
    sbom = fabric.generate_sbom()
    assert sbom.bom_format == "CycloneDX"
    assert len(sbom.components) >= 5
    assert sbom.manifest_hash != ""


def test_slsa_provenance_generation():
    fabric = SupplyChainAttestationFabric()
    slsa = fabric.generate_slsa_provenance("commit_abc123", [{"name": "pkg-a", "sha256": "digest123"}])
    assert slsa.commit_sha == "commit_abc123"
    assert slsa.predicate_type == "https://slsa.dev/provenance/v1"
    assert len(slsa.subject) == 1


def test_in_toto_envelope_synthesis_and_verification():
    fabric = SupplyChainAttestationFabric()
    envelope = fabric.synthesize_attestation_envelope("commit_407f7b5")
    assert envelope.payload_type == "application/vnd.in-toto+json"
    assert envelope.signature != ""
    assert fabric.verify_envelope(envelope) is True


def test_in_toto_envelope_tampering_rejection():
    fabric = SupplyChainAttestationFabric()
    envelope = fabric.synthesize_attestation_envelope("commit_407f7b5")

    # Tamper payload
    envelope.payload["commit_sha"] = "tampered_commit_hash"
    assert fabric.verify_envelope(envelope) is False
