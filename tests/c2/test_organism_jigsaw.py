"""Unit tests for SAGE Organism & Jigsaw Architecture Convergence Engine."""

import pytest
from sage.c2.organism_jigsaw import (
    JigsawRelationship,
    OrganismJigsawEngine,
    SubsystemRegistration,
    detect_duplicate_authorities,
    get_canonical_subsystem_catalog,
    verify_10_connective_tissue_gates,
)


def test_subsystem_catalog_taxonomy_validity():
    """Verify that every SAGE subsystem in the catalog has a valid Jigsaw taxonomy classification."""
    catalog = get_canonical_subsystem_catalog()
    assert len(catalog) >= 10

    core_count = sum(1 for s in catalog if s.relationship == JigsawRelationship.CORE)
    service_count = sum(1 for s in catalog if s.relationship == JigsawRelationship.SERVICE)
    projection_count = sum(1 for s in catalog if s.relationship == JigsawRelationship.PROJECTION)
    evidence_count = sum(1 for s in catalog if s.relationship == JigsawRelationship.EVIDENCE_LEARNING)

    assert core_count >= 3
    assert service_count >= 3
    assert projection_count >= 2
    assert evidence_count >= 3


def test_no_duplicate_authorities_detected_in_canonical_catalog():
    """Verify that canonical catalog has zero duplicate state, C2, or workflow authority claims."""
    catalog = get_canonical_subsystem_catalog()
    conflicts = detect_duplicate_authorities(catalog)
    assert conflicts == []


def test_duplicate_authority_detection_fails_closed():
    """Verify that duplicate domain registrations are correctly flagged as conflicts."""
    catalog = [
        SubsystemRegistration(
            subsystem_id="runtime_state_1",
            module_path="sage/runtime/engine.py",
            relationship=JigsawRelationship.CORE,
            description="Core runtime",
            authoritative_domain="state_authority",
        ),
        SubsystemRegistration(
            subsystem_id="shadow_state_2",
            module_path="sage/experimental/shadow.py",
            relationship=JigsawRelationship.CORE,
            description="Shadow duplicate state",
            authoritative_domain="state_authority",
        ),
    ]
    conflicts = detect_duplicate_authorities(catalog)
    assert len(conflicts) == 1
    assert "Duplicate authority detected for domain 'state_authority'" in conflicts[0]


def test_verify_10_connective_tissue_gates_structure():
    """Verify that all 10 connective tissue integration gates evaluate cleanly."""
    commit_sha = "fcf7d0c5f0345d9293bb8c15b402b7b20edf3bad"
    gates = verify_10_connective_tissue_gates(commit_sha)

    assert len(gates) == 10
    for idx, gate in enumerate(gates, 1):
        assert gate.gate_id == f"GATE-{idx}"
        assert gate.passed is True
        assert gate.evidence_ref.startswith(f"SHA256:{commit_sha[:8]}:GATE-{idx}")


def test_organism_jigsaw_engine_execution_and_receipt_verification():
    """Verify OrganismJigsawEngine execution, SHA-256 evidence generation, and cryptographic verification."""
    commit_sha = "fcf7d0c5f0345d9293bb8c15b402b7b20edf3bad"
    engine = OrganismJigsawEngine(commit_sha=commit_sha)
    receipt = engine.execute()

    assert receipt.commit_sha == commit_sha
    assert receipt.all_gates_passed is True
    assert receipt.duplicate_authorities_detected == 0
    assert receipt.gates_evaluated == 10
    assert receipt.gates_passed == 10
    assert receipt.verify() is True

    # Tamper check
    receipt_dict = receipt.model_dump()
    receipt_dict["duplicate_authorities_detected"] = 1
    from sage.c2.organism_jigsaw import OrganismVerificationReceipt
    tampered_receipt = OrganismVerificationReceipt(**receipt_dict)
    assert tampered_receipt.verify() is False
