from __future__ import annotations

import pytest

from sage.c2.execution_cell_contract import ExecutionAttestation, MissionPackage


SHA = "8e81398007b570c165122df9790de05b47407e59"


def mission() -> MissionPackage:
    return MissionPackage(
        mission_id="MIS-EXECUTION-CELL-001",
        target_repo="dariusbrandon880-art/Sage",
        canonical_head_sha=SHA,
        allowed_paths=["sage/tools/", "evidence_capture/"],
        allowed_commands=[
            "python3 -m sage.tools.generate_receipts --wave big_jump --wave multi_session --bind-head " + SHA,
            "pytest tests/c2/test_execution_cell_contract.py",
        ],
        flight_allocation={
            "f1_recon": "repo-truth",
            "f2_build": "repair",
            "f3_test": "verification",
            "f4_evidence": "attestation",
            "f5_converge": "remote-reconciliation",
        },
        collision_lock={"resource": "execution-cell-contract", "lock_acquired": True},
    )


def test_requires_exact_canonical_sha() -> None:
    with pytest.raises(ValueError):
        MissionPackage(
            mission_id="m",
            target_repo="dariusbrandon880-art/Sage",
            canonical_head_sha=SHA[:8],
            flight_allocation=mission().flight_allocation,
            collision_lock=mission().collision_lock,
        )


def test_rejects_shell_composition() -> None:
    package = mission()
    assert not package.command_allowed("pytest tests/c2/test_execution_cell_contract.py && git push")
    assert not package.command_allowed("pytest tests/c2/test_execution_cell_contract.py; git push")
    assert not package.command_allowed("pytest tests/c2/test_execution_cell_contract.py | cat")
    assert package.command_allowed(package.allowed_commands[1])


def test_path_allowlist_is_bounded() -> None:
    package = mission()
    assert package.path_allowed("sage/tools/generate_receipts.py")
    assert package.path_allowed("evidence_capture/example.json")
    assert not package.path_allowed("/tmp/example.json")
    assert not package.path_allowed("sage/tools/../runtime/engine.py")
    assert not package.path_allowed("README.md")


def test_attestation_acceptance_is_fail_closed() -> None:
    passing = ExecutionAttestation(
        mission_id=mission().mission_id,
        substrate="github_actions",
        status="PASS",
        exit_code=0,
        executed_head_sha=SHA,
        produced_head_sha=SHA,
        receipt_path="evidence_capture/execution_cell_receipt.json",
        exact_head_verified=True,
        test_pass_rate=1.0,
        collision_detected=False,
    )
    assert passing.acceptance_eligible()

    blocked = passing.model_copy(update={"exact_head_verified": False})
    assert not blocked.acceptance_eligible()


def test_shadow_boundary_rejects_wagering() -> None:
    payload = mission().model_dump()
    payload["wagering_executed"] = True
    with pytest.raises(ValueError):
        MissionPackage(**payload)


def test_execution_attestation_digest_and_mission_binding() -> None:
    pkg = mission()
    pkg_hash = pkg.compute_package_hash()
    assert len(pkg_hash) == 64

    attestation = ExecutionAttestation(
        mission_id=pkg.mission_id,
        substrate="github_actions",
        status="PASS",
        exit_code=0,
        executed_head_sha=SHA,
        produced_head_sha=SHA,
        receipt_path="evidence_capture/execution_cell_receipt.json",
        exact_head_verified=True,
        test_pass_rate=1.0,
        collision_detected=False,
        mission_package_hash=pkg_hash,
    )
    attestation.attestation_digest = attestation.compute_digest()

    assert len(attestation.attestation_digest) == 64
    assert attestation.verify_integrity() is True
    assert attestation.verify_mission_binding(pkg) is True

    # Tampered attestation digest fails integrity
    tampered_att = attestation.model_copy(update={"test_pass_rate": 0.9})
    assert tampered_att.verify_integrity() is False

    # Cross-flight mission ID mismatch fails binding
    mismatched_pkg = pkg.model_copy(update={"mission_id": "MIS-CROSS-FLIGHT-999"})
    assert attestation.verify_mission_binding(mismatched_pkg) is False

    # Stale head SHA mismatch fails binding
    stale_pkg = pkg.model_copy(update={"canonical_head_sha": "a" * 40})
    assert attestation.verify_mission_binding(stale_pkg) is False
