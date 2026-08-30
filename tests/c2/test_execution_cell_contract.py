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
    with pytest.raises(ValueError):
        mission().model_copy(update={"wagering_executed": True})
