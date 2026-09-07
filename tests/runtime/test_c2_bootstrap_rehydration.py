"""Adversarial rehydration and runtime seam tests for C2Bootstrap and SageRuntime."""

import json
from pathlib import Path
import pytest

from sage.runtime.c2_bootstrap import C2Bootstrap, C2BootResult
from sage.runtime.engine import SageRuntime


def test_c2_bootstrap_no_available_surfaces():
    """Verify boot fails closed when no execution surfaces are available."""
    bootstrap = C2Bootstrap(available_surfaces=[])
    result = bootstrap.boot(
        state_restored=True,
        runtime_validated=True,
        session_lineage_valid=True,
    )
    assert result.rehydrated is False
    assert result.direct_execution_available is False
    assert result.blocker == "No execution surface available"


def test_c2_bootstrap_state_restoration_missing():
    """Verify boot fails closed when state restoration evidence is False."""
    bootstrap = C2Bootstrap(available_surfaces=["acr", "memory"])
    result = bootstrap.boot(
        state_restored=False,
        runtime_validated=True,
        session_lineage_valid=True,
    )
    assert result.rehydrated is False
    assert result.direct_execution_available is False
    assert result.blocker == "State restoration evidence missing or invalid"


def test_c2_bootstrap_runtime_validation_failed():
    """Verify boot blocks direct execution when runtime validation fails."""
    bootstrap = C2Bootstrap(available_surfaces=["acr", "memory"])
    result = bootstrap.boot(
        state_restored=True,
        runtime_validated=False,
        session_lineage_valid=True,
    )
    assert result.rehydrated is True
    assert result.direct_execution_available is False
    assert result.blocker == "Runtime state integrity check failed"


def test_c2_bootstrap_session_lineage_broken():
    """Verify boot blocks direct execution when session lineage is invalid."""
    bootstrap = C2Bootstrap(available_surfaces=["acr", "memory"])
    result = bootstrap.boot(
        state_restored=True,
        runtime_validated=True,
        session_lineage_valid=False,
    )
    assert result.rehydrated is True
    assert result.direct_execution_available is False
    assert result.blocker == "Session lineage continuity broken or missing"


def test_c2_bootstrap_all_valid():
    """Verify boot permits direct execution when all rehydration evidence checks pass."""
    bootstrap = C2Bootstrap(available_surfaces=["acr", "memory"])
    restoration_ev = {"state_file": "sage_data/state.json"}
    readiness_ev = {"integrity_is_valid": True}
    result = bootstrap.boot(
        state_restored=True,
        runtime_validated=True,
        session_lineage_valid=True,
        restoration_evidence=restoration_ev,
        readiness_evidence=readiness_ev,
    )
    assert result.rehydrated is True
    assert result.direct_execution_available is True
    assert result.blocker is None
    assert result.restoration_evidence == restoration_ev
    assert result.readiness_evidence == readiness_ev


def test_sageruntime_verify_execution_permitted_success(tmp_path):
    """Verify SageRuntime allows execution when boot readiness passes."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))
    assert runtime.verify_execution_permitted() is True


def test_sageruntime_corrupted_state_file_blocks_execution(tmp_path):
    """Adversarial test: corrupted state file marks state_restored=False and blocks execution."""
    workspace = tmp_path / "sage_data"
    workspace.mkdir(parents=True)
    state_file = workspace / "state.json"
    state_file.write_text("{corrupted_json: bad_syntax")

    runtime = SageRuntime(workspace_path=str(workspace))
    assert runtime.c2_boot_result.rehydrated is False
    assert runtime.c2_boot_result.direct_execution_available is False
    assert runtime.c2_boot_result.blocker == "State restoration evidence missing or invalid"

    with pytest.raises(RuntimeError, match="State restoration evidence missing or invalid"):
        runtime.verify_execution_permitted()


def test_sageruntime_corrupted_workspace_file_blocks_execution(tmp_path):
    """Adversarial test: corrupted JSON file in workspace causes verify_integrity to fail and blocks execution."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))

    # Plant corrupted file in memory store
    corrupted_file = runtime.memory_path / "corrupted_memory.json"
    corrupted_file.write_text("{invalid: json}")

    runtime.refresh_c2_bootstrap()
    assert runtime.c2_boot_result.rehydrated is True
    assert runtime.c2_boot_result.direct_execution_available is False
    assert runtime.c2_boot_result.blocker == "Runtime state integrity check failed"

    with pytest.raises(RuntimeError, match="Runtime state integrity check failed"):
        runtime.verify_execution_permitted()


def test_sageruntime_broken_lineage_blocks_execution(tmp_path):
    """Adversarial test: active objective without session lineage causes lineage_valid=False and blocks execution."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))

    # Set objective directly in current_state without ACR lineage
    runtime.current_state.current_objective = "Unlinked objective"
    runtime.refresh_c2_bootstrap()

    assert runtime.c2_boot_result.rehydrated is True
    assert runtime.c2_boot_result.direct_execution_available is False
    assert runtime.c2_boot_result.blocker == "Session lineage continuity broken or missing"

    with pytest.raises(RuntimeError, match="Session lineage continuity broken or missing"):
        runtime.verify_execution_permitted()


def test_sageruntime_failed_restore_session_blocks_execution(tmp_path):
    """Adversarial test: attempting to restore from non-existent file sets state_restored=False."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))

    success = runtime.restore_session(str(workspace / "missing_handoff.json"))
    assert success is False
    assert runtime.c2_boot_result.rehydrated is False
    assert runtime.c2_boot_result.direct_execution_available is False

    with pytest.raises(RuntimeError, match="State restoration evidence missing or invalid"):
        runtime.verify_execution_permitted()


def test_sageruntime_successful_handoff_restoration_permits_execution(tmp_path):
    """Verify session handoff export and restoration rehydrates valid execution readiness."""
    workspace1 = tmp_path / "workspace1"
    runtime1 = SageRuntime(workspace_path=str(workspace1))
    runtime1.set_objective("Objective Alpha")
    runtime1.set_task("Task 1")
    handoff_path = runtime1.generate_handoff()

    workspace2 = tmp_path / "workspace2"
    runtime2 = SageRuntime(workspace_path=str(workspace2))
    restored = runtime2.restore_session(handoff_path)

    assert restored is True
    assert runtime2.current_state.current_objective == "Objective Alpha"
    assert runtime2.current_state.active_task == "Task 1"
    assert runtime2.c2_boot_result.rehydrated is True
    assert runtime2.c2_boot_result.direct_execution_available is True
    assert runtime2.verify_execution_permitted() is True


def test_sageruntime_snapshot_roundtrip_preserves_rehydration_readiness(tmp_path):
    """Verify workspace snapshot create and restore maintains rehydration readiness."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))
    runtime.set_objective("Snapshot Objective")
    snapshot_id = runtime.create_workspace_snapshot()

    # Modify state in workspace
    runtime.set_objective("Mutated Objective")
    assert runtime.current_state.current_objective == "Mutated Objective"

    # Restore snapshot
    restored = runtime.restore_workspace_snapshot(snapshot_id)
    assert restored is True
    assert runtime.current_state.current_objective == "Snapshot Objective"
    assert runtime.c2_boot_result.rehydrated is True
    assert runtime.c2_boot_result.direct_execution_available is True
    assert runtime.verify_execution_permitted() is True


def test_sagi_cognition_observes_without_state_mutation(tmp_path):
    """Verify cognitive observation via export_all/get_status does not alter state authority."""
    workspace = tmp_path / "sage_data"
    runtime = SageRuntime(workspace_path=str(workspace))
    runtime.set_objective("Cognitive Observation Objective")

    # Cognitive observation
    status = runtime.get_status()
    exported = runtime.export_all()
    summary = runtime.get_active_capability_summary()

    # Confirm canonical runtime state is intact and unmutated
    assert status["current_objective"] == "Cognitive Observation Objective"
    assert exported["state"]["current_objective"] == "Cognitive Observation Objective"
    assert summary["c2_rehydrated"] is True
    assert runtime.current_state.current_objective == "Cognitive Observation Objective"
