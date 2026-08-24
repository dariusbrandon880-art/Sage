"""Unit and adversarial tests for AuthorizationPackageSynthesizer."""

from __future__ import annotations

import pytest

from sage.c2.authorization_package_synthesis import (
    AuthorizationPackageSynthesizer,
    compute_package_hash,
)


def test_evaluate_risk_surface_safe_candidate():
    synth = AuthorizationPackageSynthesizer(commit_sha="commit_test_100")
    surface = synth.evaluate_risk_surface(
        candidate_id="cand_safe_01",
        target_paths=("sage/experimental/airspace/models.py",),
        evidence_requirements=("git_commit", "test_report"),
        verification_plan_present=True,
    )

    assert surface.candidate_id == "cand_safe_01"
    assert surface.risk_verdict == "SAFE"
    assert not surface.protected_paths
    assert surface.verification_plan_present is True


def test_evaluate_risk_surface_blocked_protected_path():
    synth = AuthorizationPackageSynthesizer(commit_sha="commit_test_100")
    surface = synth.evaluate_risk_surface(
        candidate_id="cand_blocked_02",
        target_paths=("sage/runtime/engine.py",),
        verification_plan_present=True,
    )

    assert surface.candidate_id == "cand_blocked_02"
    assert surface.risk_verdict == "BLOCKED"
    assert "sage/runtime/engine.py" in surface.protected_paths


def test_synthesize_package_defaults_to_unauthorized():
    synth = AuthorizationPackageSynthesizer(commit_sha="commit_test_100")
    pkg = synth.synthesize_package(
        candidate_id="cand_unapproved_03",
        target_paths=("sage/experimental/a.py",),
        verification_plan_present=True,
        authorization_token=None,  # No C2 token
    )

    assert pkg.candidate_id == "cand_unapproved_03"
    assert pkg.is_authorized is False
    assert pkg.authorization_status == "UNAPPROVED_DEFAULT"


def test_synthesize_package_approved_with_c2_token():
    synth = AuthorizationPackageSynthesizer(commit_sha="commit_test_100")
    pkg = synth.synthesize_package(
        candidate_id="cand_approved_04",
        target_paths=("sage/experimental/a.py",),
        verification_plan_present=True,
        authorization_token="c2_token_valid_2026",
    )

    assert pkg.candidate_id == "cand_approved_04"
    assert pkg.is_authorized is True
    assert pkg.authorization_status == "AUTHORIZED_BY_C2"
    assert pkg.authorization_token == "c2_token_valid_2026"


def test_synthesize_package_blocked_without_verification_plan():
    synth = AuthorizationPackageSynthesizer(commit_sha="commit_test_100")
    pkg = synth.synthesize_package(
        candidate_id="cand_no_plan_05",
        target_paths=("sage/experimental/a.py",),
        verification_plan_present=False,  # Missing verification plan
        authorization_token="c2_token_valid_2026",
    )

    assert pkg.candidate_id == "cand_no_plan_05"
    assert pkg.is_authorized is False
    assert pkg.authorization_status == "BLOCKED_MISSING_VERIFICATION_PLAN"


def test_empty_candidate_id_raises_value_error():
    synth = AuthorizationPackageSynthesizer()
    with pytest.raises(ValueError, match="candidate_id is required"):
        synth.evaluate_risk_surface(candidate_id="", target_paths=("sage/experimental/a.py",))


def test_package_hash_determinism():
    h1 = compute_package_hash("cand_1", 0.1, True, "tok_1", "sha_1")
    h2 = compute_package_hash("cand_1", 0.1, True, "tok_1", "sha_1")
    h3 = compute_package_hash("cand_1", 0.1, False, "tok_1", "sha_1")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
