"""Unit and Integration Tests for SAGE-ACH (Active Client Hook)."""

import os
import shutil
import tempfile
import pytest
import re
from pydantic import BaseModel
from sage.experimental.act.active_hook import (
    ActiveInterceptHookEvent,
    ActiveClientHook,
)
from sage.experimental.act.continuity_control import ContinuityControlLoop


@pytest.fixture
def temp_stage_dir():
    """Fixture to provide a clean, temporary staging directory for testing SAGE-CCL."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_mock_command_execution(temp_stage_dir):
    """Verify that safe commands are spawned, and their duration, output, and code are captured."""
    hook = ActiveClientHook()
    session_id = "session_11112222"

    # We use a simple echo command to execute without shell injection risks
    # python -c "print('SAGE-ACH_TEST')" is multi-platform compliant
    command = "python -c print('SAGE-ACH_TEST')"
    event = hook.execute_observed_command(
        session_id=session_id,
        command=command,
        target_files=[],
    )

    assert isinstance(event, ActiveInterceptHookEvent)
    assert event.command == command
    assert event.exit_code == 0
    assert event.execution_duration > 0.0
    assert "SAGE-ACH_TEST" in event.output_summary
    assert re.match(r"^ACH-EVT-[0-9]{8}-[a-fA-F0-9\-]{36}$", event.event_id)
    assert event.linked_record_id is None


def test_command_execution_failure():
    """Verify that missing commands are gracefully captured with error codes."""
    hook = ActiveClientHook()
    session_id = "session_33334444"

    # Execution of a completely invalid process command
    command = "non_existent_command_xyz123"
    event = hook.execute_observed_command(
        session_id=session_id,
        command=command,
        target_files=[],
    )

    assert isinstance(event, ActiveInterceptHookEvent)
    assert event.exit_code == -2
    assert "Process spawn failed" in event.output_summary


def test_state_shift_differential_tracking(temp_stage_dir):
    """Verify that file state modifications are captured as SHA differentials."""
    hook = ActiveClientHook()
    session_id = "session_55556666"

    # Create temporary file to monitor
    test_filepath = os.path.join(temp_stage_dir, "observe_target.txt")
    with open(test_filepath, "w") as f:
        f.write("Initial state")

    # Command writes new content to the file
    command = f"python -c open('{test_filepath}','w').write('Modified_state')"

    event = hook.execute_observed_command(
        session_id=session_id,
        command=command,
        target_files=[test_filepath],
    )

    assert test_filepath in event.workspace_before
    assert test_filepath in event.workspace_after
    assert event.workspace_before[test_filepath] != event.workspace_after[test_filepath]


def test_ccl_automatic_record_streaming_and_linking(temp_stage_dir):
    """Verify that executing a command automatically streams and links records to SAGE-CCL."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    hook = ActiveClientHook(ccl_loop=ccl)
    session_id = "session_88889999"

    command = "python -c print('STREAM_TEST')"
    event = hook.execute_observed_command(
        session_id=session_id,
        command=command,
        target_files=[],
    )

    # Assert record is linked
    assert event.linked_record_id is not None
    assert re.match(r"^CCL-REC-[0-9]{8}-[a-fA-F0-9\-]{36}$", event.linked_record_id)

    # Check CCL record was staged
    verify_res = ccl.verify_record_integrity(event.linked_record_id)
    assert verify_res["status"] == "VERIFIED_STABLE"


def test_ccl_automatic_failure_context_logging(temp_stage_dir):
    """Verify that command execution failures append failing contexts to CCL records."""
    ccl = ContinuityControlLoop(stage_dir=temp_stage_dir)
    hook = ActiveClientHook(ccl_loop=ccl)
    session_id = "session_aaaabbbb"

    # Force a process spawn failure
    command = "failing_command_abc"
    event = hook.execute_observed_command(
        session_id=session_id,
        command=command,
        target_files=[],
    )

    # Check CCL record failure context
    records = ccl.list_records(session_id=session_id)
    assert len(records) == 1
    rec = records[0]

    assert rec.failure_context is not None
    assert rec.failure_context["error_type"] == "CommandExecutionFailure"
    assert rec.failure_context["exit_code"] == -2
    assert "Process spawn failed" in rec.failure_context["details"]
    assert rec.recovery_path is not None


def test_one_way_import_isolation_enforcement():
    """Assert that core production layers do not import SAGE-ACH experimental code."""
    production_dirs = ["sage/runtime", "sage/core", "sage/acr"]
    experimental_import_pattern = re.compile(r"sage\.experimental\.act\.active_hook")

    for p_dir in production_dirs:
        if not os.path.exists(p_dir):
            continue
        for root, _, files in os.walk(p_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                    if experimental_import_pattern.search(content):
                        pytest.fail(
                            f"One-Way Import Law Violation: Production file '{filepath}' "
                            f"imports from experimental 'sage.experimental.act.active_hook'."
                        )
