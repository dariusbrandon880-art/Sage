"""Validation tests for SAGEMissionExecutionBridge.

Verifies the complete real workspace -> impact analysis -> revalidation -> result -> measurement execution flow
covering Cognitive Safety Gating, safety recovery, and cryptographic receipts.
"""

import os
import json
import pytest
import shutil
import hashlib
from pathlib import Path

from sage.experimental.mission_control_bridge import (
    SAGEMissionExecutionBridge,
    WorkloadResult,
    CapabilityRevalidationRecord,
    SAGEWorkloadReceiptChain
)
from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
)


@pytest.fixture
def test_setup(tmp_path):
    """Isolates the operational registry, archive, and evidence logs for test runs."""
    original_registry = Path("evidence_capture/operational_capability_registry.json")
    temp_registry = tmp_path / "operational_capability_registry.json"

    # Copy the registry to allow modifications without affecting workspace baseline
    shutil.copy(original_registry, temp_registry)

    # Output lineage file path
    lineage_file = tmp_path / "workspace_revalidation_evidence.json"

    return {
        "registry_path": str(temp_registry),
        "lineage_path": str(lineage_file),
        "tmp_path": tmp_path
    }


def test_mission_control_bridge_end_to_end_safe(test_setup):
    """Verify the safe end-to-end execution pathway with Cognitive Safety Gating passing."""
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]

    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)

    # Use tests/test_continuity_bridge.py which is modified
    modified_files = ["tests/test_continuity_bridge.py"]

    # Execute the bridge pipeline
    report = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-test-bridge-revalidation",
        lineage_output_path=lineage_path
    )

    # Verify pipeline outcome structures
    assert "git_head_hash" in report
    assert report["changed_artifacts"] == modified_files
    assert report["predicted_impact"]["revalidation_required"] is True

    # Check workload execution
    workloads = report["selected_workloads"]
    assert len(workloads) == 1
    assert workloads[0]["status_updated_to"] == "VALIDATED"

    # Check state transitions completed cleanly up to CLOSED
    assert report["state_progression"]["terminal_state"] == "CLOSED"

    # Confirm cryptographic receipts chaining is correct
    assert "receipts_chain" in report
    assert len(report["receipts_chain"]) > 0
    receipt = report["receipts_chain"][-1]
    assert receipt["parent_hash"] == "GENESIS_ROOT"
    assert "signature" in receipt

    # Confirm permanent Master Archive promotion is successful
    archive_files = list(Path("sage_data/archive").glob("*.json"))
    assert len(archive_files) > 0


def test_mission_control_bridge_unsafe_halt(test_setup):
    """Verify that an unsafe CognitiveState halts execution at PREFLIGHT_REQUIRED."""
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]

    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)

    # Construct an unsafe CognitiveState (low confidence)
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="msn-unsafe-01",
        objective="Verify continuous integration revalidation paths on workspace changes",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(
        authorized_agents=["agent_jules_sage"]
    )
    # 0.1 confidence triggers LOW_CONFIDENCE block/clarification in PFC Safety Gate
    confidence = CognitiveConfidenceState(
        overall_confidence=0.1,
        last_updated=0.0
    )
    next_action = CognitiveNextAction(
        action_id="task_workspace_revalidation",
        description="Verify integration paths on workspace changes",
        assigned_agent="agent_jules_sage"
    )
    unsafe_cognitive_state = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action
    )

    modified_files = ["tests/test_continuity_bridge.py"]

    # Execute and verify execution halts at PREFLIGHT_REQUIRED
    report = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-unsafe-01",
        cognitive_state=unsafe_cognitive_state,
        lineage_output_path=lineage_path
    )

    assert report["state_progression"]["terminal_state"] == "PREFLIGHT_REQUIRED"
    assert report["actual_results"]["success"] is False
    assert "cognitive_safety_block" in report["actual_results"]
    assert report["actual_results"]["cognitive_safety_block"]["outcome"] == "REQUEST_CLARIFICATION"


def test_mission_control_bridge_recovery(test_setup):
    """Verify Safety-Gated Recovery where corrected CognitiveState unblocks execution."""
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]

    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)

    # Corrected CognitiveState with high confidence (1.0)
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="msn-recovery-01",
        objective="Verify continuous integration revalidation paths on workspace changes",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(
        authorized_agents=["agent_jules_sage"]
    )
    confidence = CognitiveConfidenceState(
        overall_confidence=1.0,
        last_updated=0.0
    )
    next_action = CognitiveNextAction(
        action_id="task_workspace_revalidation",
        description="Verify integration paths on workspace changes",
        assigned_agent="agent_jules_sage"
    )
    corrected_cognitive_state = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action
    )

    modified_files = ["tests/test_continuity_bridge.py"]

    # Execute recovery flow
    report = bridge.recover_from_cognitive_block(
        corrected_cognitive_state=corrected_cognitive_state,
        modified_files=modified_files,
        mission_id="msn-recovery-01",
        lineage_output_path=lineage_path
    )

    # Confirm progression succeeds up to CLOSED
    assert report["state_progression"]["terminal_state"] == "CLOSED"
    assert report["actual_results"]["success"] is True
    assert report["actual_results"]["recovery_triggered"] is True


def test_cryptographic_receipt_chaining(test_setup):
    """Verify cryptographic workload receipts link sequentially using SHA-256 parent signatures."""
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]

    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)
    modified_files = ["tests/test_continuity_bridge.py"]

    # 1. Run first pipeline
    report1 = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-chain-01",
        lineage_output_path=lineage_path
    )
    r1 = report1["receipts_chain"][-1]
    assert r1["parent_hash"] == "GENESIS_ROOT"

    # 2. Run second pipeline
    report2 = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-chain-02",
        lineage_output_path=lineage_path
    )
    r2 = report2["receipts_chain"][-1]
    # Signature of block 1 should cleanly match parent_hash of block 2
    assert r2["parent_hash"] == r1["signature"]


def test_cli_audit_subcommands(test_setup):
    """Verify SAGE CLI 'audit' subcommands render summary, diagnostics, and scan."""
    from unittest.mock import patch
    from sage.cli import main as cli_main

    # Build a sample archived entry first
    registry_path = test_setup["registry_path"]
    lineage_path = test_setup["lineage_path"]
    bridge = SAGEMissionExecutionBridge(registry_path=registry_path)
    bridge.execute_workspace_pipeline(
        modified_files=["tests/test_continuity_bridge.py"],
        mission_id="msn-cli-audit-sample",
        lineage_output_path=lineage_path
    )

    with patch("sys.argv", ["sage-cli", "audit", "--action", "summary"]):
        with patch("builtins.print") as mock_print:
            cli_main()
            printed = "".join([args[0] for args, _ in mock_print.call_args_list])
            assert "SAGE ACT-PROD ACTIVE WORKSPACE TRACES" in printed
            assert "[HEALTHY]" in printed

    with patch("sys.argv", ["sage-cli", "audit", "--action", "diagnostics"]):
        with patch("builtins.print") as mock_print:
            cli_main()
            printed = "".join([args[0] for args, _ in mock_print.call_args_list])
            assert "SAGE ACT-PROD DIAGNOSTICS & AUDIT" in printed

    with patch("sys.argv", ["sage-cli", "audit", "--action", "scan"]):
        with patch("builtins.print") as mock_print:
            cli_main()
            printed = "".join([args[0] for args, _ in mock_print.call_args_list])
            assert "SAGE CAPABILITY VALIDATION STATUS" in printed
