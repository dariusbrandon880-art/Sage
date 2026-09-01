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


def passing_attestation(package: MissionPackage) -> ExecutionAttestation:
    return ExecutionAttestation(
        mission_id=package.mission_id,
        mission_package_digest=package.package_digest(),
        substrate="github_actions",
        status="PASS",
        exit_code=0,
        executed_head_sha=package.canonical_head_sha,
        produced_head_sha=package.canonical_head_sha,
        receipt_path="evidence_capture/execution_cell_receipt.json",
        exact_head_verified=True,
        test_pass_rate=1.0,
        collision_detected=False,
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


def test_attestation_requires_exact_mission_binding() -> None:
    package = mission()
    passing = passing_attestation(package)
    assert passing.verify_mission_binding(package)
    assert passing.acceptance_eligible(package)


def test_attestation_rejects_tampered_mission_package() -> None:
    package = mission()
    passing = passing_attestation(package)
    tampered = package.model_copy(update={"allowed_paths": ["/tmp"]})
    assert not passing.verify_mission_binding(tampered)
    assert not passing.acceptance_eligible(tampered)


def test_attestation_rejects_mission_identity_swap() -> None:
    package = mission()
    passing = passing_attestation(package)
    swapped = package.model_copy(update={"mission_id": "MIS-SPOOFED"})
    assert not passing.verify_mission_binding(swapped)
    assert not passing.acceptance_eligible(swapped)


def test_attestation_rejects_exact_head_mismatch() -> None:
    package = mission()
    passing = passing_attestation(package).model_copy(
        update={"executed_head_sha": "0" * 40}
    )
    assert not passing.verify_mission_binding(package)
    assert not passing.acceptance_eligible(package)


def test_attestation_rejects_produced_head_drift() -> None:
    package = mission()
    passing = passing_attestation(package).model_copy(
        update={"produced_head_sha": "1" * 40}
    )
    assert not passing.verify_mission_binding(package)
    assert not passing.acceptance_eligible(package)


def test_attestation_without_binding_is_fail_closed() -> None:
    package = mission()
    passing = passing_attestation(package).model_copy(update={"mission_package_digest": None})
    assert not passing.acceptance_eligible(package)


def test_attestation_acceptance_is_fail_closed() -> None:
    package = mission()
    passing = passing_attestation(package)
    assert passing.acceptance_eligible(package)

    blocked = passing.model_copy(update={"exact_head_verified": False})
    assert not blocked.acceptance_eligible(package)


def test_shadow_boundary_rejects_wagering() -> None:
    payload = mission().model_dump()
    payload["wagering_executed"] = True
    with pytest.raises(ValueError):
        MissionPackage(**payload)
