"""Unit and adversarial tests for SAGE Supply Chain Attestation & Provenance Fabric."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from sage.c2.supply_chain_attestation import (
    SupplyChainAttestationFabric,
    SupplyChainAttestation,
)


def test_supply_chain_attestation_creation_and_validation() -> None:
    fabric = SupplyChainAttestationFabric()
    attestation = fabric.create_attestation(
        target_name="test_target_package",
        test_pass_count=889,
    )

    data = attestation.to_dict()

    assert data["_type"] == "https://in-toto.io/Statement/v1"
    assert data["subject"]["name"] == "test_target_package"
    assert data["provenance"]["predicate_type"] == "https://slsa.dev/provenance/v1"
    assert data["provenance"]["verification_test_pass_count"] == 889
    assert len(data["signature_digest"]) == 64

    is_valid, violations = SupplyChainAttestationFabric.validate_attestation(data)
    assert is_valid is True
    assert violations == []


def test_supply_chain_attestation_detects_tampering() -> None:
    fabric = SupplyChainAttestationFabric()
    attestation = fabric.create_attestation(
        target_name="tamper_test_package",
        test_pass_count=889,
    )

    data = attestation.to_dict()

    # Tamper with invocation steps in provenance
    data["provenance"]["invocation_steps"].append("unauthorized_injection_step")

    is_valid, violations = SupplyChainAttestationFabric.validate_attestation(data)
    assert is_valid is False
    assert any("ATTESTATION_TAMPERED" in v for v in violations)


def test_supply_chain_attestation_runner_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.execute_supply_chain_attestation import main

    monkeypatch.setattr("scripts.execute_supply_chain_attestation.REPO_ROOT", tmp_path)

    main()

    evidence_file = tmp_path / "evidence_capture" / "supply_chain_attestation.json"
    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["_type"] == "https://in-toto.io/Statement/v1"
    assert data["attestation_status"] == "VERIFIED_SECURE"
    assert len(data["signature_digest"]) == 64
