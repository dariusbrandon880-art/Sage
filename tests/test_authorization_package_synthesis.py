import pytest

from sage.c2.authorization_package_synthesis import (
    AuthorizationPackageSynthesizer,
    AuthorizationPackage,
    RiskSurface,
    VerificationObligation,
)


def test_synthesize_valid_authorization_package():
    synthesizer = AuthorizationPackageSynthesizer()
    candidate = {
        "candidate_id": "cand_synthesize_001",
        "description": "Synthesize Authorization Package Test",
        "provenance_ref": "ref_prov_001",
        "dependency_graph": {"cand_synthesize_001": ["dep_a", "dep_b"]},
        "affected_namespaces": ["sage/c2/"],
        "risk_score": 0.3,
        "prerequisites": {"dep_a": True, "dep_b": True},
    }

    pkg = synthesizer.synthesize_package(candidate, authorized_ids=("cand_synthesize_001",))

    assert pkg.candidate_id == "cand_synthesize_001"
    assert pkg.is_authorized is True
    assert pkg.risk_surface.score == 0.3
    assert pkg.risk_surface.protected_boundary_crossing is False
    assert len(pkg.package_digest) == 64


def test_fail_closed_on_unfulfilled_prerequisite():
    synthesizer = AuthorizationPackageSynthesizer()
    candidate = {
        "candidate_id": "cand_synthesize_002",
        "description": "Unfulfilled Prerequisite Candidate",
        "provenance_ref": "ref_prov_002",
        "affected_namespaces": ["sage/c2/"],
        "prerequisites": {"prereq_approved": False},
    }

    pkg = synthesizer.synthesize_package(candidate, authorized_ids=("cand_synthesize_002",))

    assert pkg.is_authorized is False
    assert pkg.risk_surface.score == 1.0


def test_fail_closed_on_protected_namespace_crossing():
    synthesizer = AuthorizationPackageSynthesizer()
    candidate = {
        "candidate_id": "cand_synthesize_003",
        "description": "Protected Core Namespace Candidate",
        "provenance_ref": "ref_prov_003",
        "affected_namespaces": ["sage/core/"],  # Protected namespace
        "risk_score": 0.2,
    }

    pkg = synthesizer.synthesize_package(candidate, authorized_ids=("cand_synthesize_003",))

    assert pkg.is_authorized is False  # Risk surface elevated to 0.85 >= 0.8 gate
    assert pkg.risk_surface.protected_boundary_crossing is True
    assert pkg.risk_surface.score >= 0.85


def test_adversarial_escalation_attempt_rejection():
    synthesizer = AuthorizationPackageSynthesizer()
    candidate = {
        "candidate_id": "cand_unauthorized_attacker",
        "description": "Adversarial Candidate Injection",
        "provenance_ref": "ref_prov_fake",
        "affected_namespaces": ["sage/runtime/"],
    }

    pkg = synthesizer.synthesize_package(candidate, authorized_ids=("legitimate_cand_001",))

    assert pkg.is_authorized is False
    assert len(pkg.package_digest) == 64
