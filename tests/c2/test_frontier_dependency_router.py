"""Unit tests for sage.c2.frontier_dependency_router."""

from __future__ import annotations

import pytest

from sage.c2.frontier_dependency_router import (
    FrontierDependencyRouter,
    compute_package_hash,
    compute_risk_fingerprint,
)


def test_evaluate_risk_low_risk_candidate():
    router = FrontierDependencyRouter(commit_sha="sha_test_123")
    profile = router.evaluate_risk(
        candidate_id="cand_exp_01",
        target_paths=("sage/experimental/new_feature.py", "tests/experimental/test_new_feature.py"),
        dependency_edges=("sage.experimental.sagi",),
        base_consequentiality=0.2,
    )

    assert profile.candidate_id == "cand_exp_01"
    assert profile.risk_level == "LOW"
    assert not profile.protected_path_touches
    assert profile.dependency_edges == ("sage.experimental.sagi",)
    assert not profile.requires_operator_override
    assert len(profile.fingerprint) == 64


def test_evaluate_risk_high_risk_protected_path_touch():
    router = FrontierDependencyRouter(commit_sha="sha_test_123")
    profile = router.evaluate_risk(
        candidate_id="cand_protected_02",
        target_paths=("sage/core/spek.py", "sage/runtime/engine.py"),
        dependency_edges=("sage.core", "sage.runtime"),
        base_consequentiality=0.8,
    )

    assert profile.candidate_id == "cand_protected_02"
    assert profile.risk_level in ("HIGH", "CRITICAL")
    assert "sage/core/spek.py" in profile.protected_path_touches
    assert "sage/runtime/engine.py" in profile.protected_path_touches
    assert profile.requires_operator_override


def test_prepare_authorization_package_high_risk_blocked_without_token():
    router = FrontierDependencyRouter(commit_sha="sha_test_123")
    profile = router.evaluate_risk(
        candidate_id="cand_high_risk",
        target_paths=("sage/runtime/engine.py",),
        base_consequentiality=0.9,
    )

    pkg = router.prepare_authorization_package(profile)

    assert pkg.candidate_id == "cand_high_risk"
    assert not pkg.authorization_ready
    assert pkg.c2_authorization_status == "BLOCKED"
    assert pkg.authorization_token == "UNAUTHORIZED_HIGH_RISK"
    assert pkg.authorized_by == "PENDING_OPERATOR_REVIEW"


def test_prepare_authorization_package_high_risk_authorized_with_token():
    router = FrontierDependencyRouter(commit_sha="sha_test_123")
    profile = router.evaluate_risk(
        candidate_id="cand_high_risk",
        target_paths=("sage/runtime/engine.py",),
        base_consequentiality=0.9,
    )

    pkg = router.prepare_authorization_package(
        profile,
        authorized_by="c2_supervisor_01",
        authorization_token="auth_override_token_777",
    )

    assert pkg.candidate_id == "cand_high_risk"
    assert pkg.authorization_ready
    assert pkg.c2_authorization_status == "AUTHORIZED"
    assert pkg.authorization_token == "auth_override_token_777"
    assert pkg.authorized_by == "c2_supervisor_01"


def test_empty_candidate_id_raises_value_error():
    router = FrontierDependencyRouter()
    with pytest.raises(ValueError, match="candidate_id is required"):
        router.evaluate_risk(candidate_id="", target_paths=("sage/experimental/a.py",))


def test_fingerprint_and_package_hash_determinism():
    f1 = compute_risk_fingerprint("cand_1", 0.5, ("path_a",), ("edge_a",))
    f2 = compute_risk_fingerprint("cand_1", 0.5, ("path_a",), ("edge_a",))
    f3 = compute_risk_fingerprint("cand_1", 0.6, ("path_a",), ("edge_a",))

    assert f1 == f2
    assert f1 != f3

    p1 = compute_package_hash("cand_1", "AUTHORIZED", "tok_1", "commit_1")
    p2 = compute_package_hash("cand_1", "AUTHORIZED", "tok_1", "commit_1")
    p3 = compute_package_hash("cand_1", "AUTHORIZED", "tok_1", "commit_2")

    assert p1 == p2
    assert p1 != p3
