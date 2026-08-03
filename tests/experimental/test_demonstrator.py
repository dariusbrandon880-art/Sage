"""Unit test suite for SAGE Enterprise Audit & Continuity Intelligence Demonstrator."""

import os
import json
import pytest
from sage.experimental.act.demonstrator import (
    DemonstratorDataIntake,
    AuditLineageVisualizer,
    DivergenceVisibilityDisplay,
    RecoveryCheckpointVisibility,
    ReceiptVerificationDisplay,
    SAGEEnterpriseDemonstrator
)


def test_demonstrator_data_intake(tmp_path):
    """Verify that demonstrator intake handles files correctly, including missing file fallbacks."""
    missing_file = tmp_path / "nonexistent.json"
    intake = DemonstratorDataIntake(context_guard_path=str(missing_file))

    # Verify fallbacks are returned for missing/corrupted files
    fallback_guard = intake.load_context_guard_evidence()
    assert fallback_guard["compliance_pack_id"] == "comp_s_guard_001"
    assert fallback_guard["decision_record"]["decision_state"] == "REJECTED"

    sdr_outputs = intake.load_sdr_004_divergence_outputs()
    assert sdr_outputs["simulation_id"] == "sim_sdr004_dem_01"

    crc_outputs = intake.load_crc_20_receipt_verification_outputs()
    assert crc_outputs["verification_status"] == "SIGNATURE_VERIFIED"


def test_demonstrator_data_intake_from_valid_file(tmp_path):
    """Verify that demonstrator intake loads valid files correctly."""
    valid_file = tmp_path / "context_guard_evidence.json"
    mock_data = {
        "session_id": "session_custom_001",
        "timestamp": "2026-08-03T10:00:00Z",
        "intake_details": {"modified_files": ["tests/test_spek.py"]},
        "protection_evaluation": {"status": "CLEAN_WORKSPACE", "severity": "LOW"},
        "decision_record": {
            "checkpoint_id": "chk_custom",
            "decision_state": "AUTO_AUTHORIZED",
            "supervisor_id": "SYSTEM_AUTO",
            "comments": "Approved.",
            "action_taken": "COMMIT_APPROVED"
        }
    }
    with open(valid_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    intake = DemonstratorDataIntake(context_guard_path=str(valid_file))
    loaded = intake.load_context_guard_evidence()
    assert loaded["session_id"] == "session_custom_001"
    assert loaded["decision_record"]["decision_state"] == "AUTO_AUTHORIZED"


def test_visualizers_and_displays():
    """Verify text visualizations build correctly."""
    guard_data = {
        "session_id": "session_visualizer_test",
        "timestamp": "2026-08-03T12:00:00Z",
        "intake_details": {
            "modified_files": ["sage/runtime/engine.py"]
        },
        "protection_evaluation": {
            "status": "PROTECTION_VIOLATION_DETECTED",
            "severity": "HIGH"
        },
        "decision_record": {
            "checkpoint_id": "chk_test_vis",
            "decision_state": "REJECTED",
            "supervisor_id": "human_supervisor_01",
            "comments": "Edit rejected.",
            "action_taken": "COMMIT_REJECTED"
        },
        "attestation": {
            "data_hash": "hash_xyz",
            "signature": "sig_abc"
        }
    }

    # 1. Audit Lineage
    vis = AuditLineageVisualizer()
    trace = vis.build_lineage_trace(guard_data)
    trace_text = "\n".join(trace)
    assert "=== SAGE CHRONOLOGICAL AUDIT LINEAGE ===" in trace_text
    assert "session_visualizer_test" in trace_text
    assert "PROTECTION_VIOLATION_DETECTED" in trace_text
    assert "COMMIT_REJECTED" in trace_text

    # 2. Checkpoint Visibility
    chk_vis = RecoveryCheckpointVisibility()
    chk_map = chk_vis.build_checkpoint_map(guard_data)
    chk_text = "\n".join(chk_map)
    assert "=== RECOVERY CHECKPOINT & SUPERVISOR SIGS ===" in chk_text
    assert "chk_test_vis" in chk_text
    assert "human_supervisor_01" in chk_text
    assert "sig_abc" in chk_text


def test_divergence_visibility_display():
    """Verify state divergence visibility rendering."""
    sdr_data = {
        "simulation_id": "sim_sdr_vis_test",
        "divergence_details": {
            "original_session_id": "session_sdr_vis",
            "diverged_branches": ["branch_a", "branch_b"],
            "diverged_agents": ["agent_a", "agent_b"]
        },
        "conflict_detection_report": {
            "conflicts_found": 1,
            "anomalies_found": 1,
            "conflicts": [{
                "conflict_type": "TASK_MUTATION_OVERRIDE",
                "task_id": "task_conf",
                "fields_mismatched": ["actor_id"],
                "details": "Details of conflict"
            }],
            "anomalies": [{
                "anomaly_type": "RELATIONAL_LOOP_DETECTED",
                "branch": "branch_a",
                "task_id": "task_loop",
                "details": "Details of loop"
            }]
        },
        "resolution_details": {
            "applied_strategy": "CHRONOLOGICAL_PRIORITY",
            "status": "RESOLVED"
        }
    }

    display = DivergenceVisibilityDisplay()
    summary = display.build_divergence_summary(sdr_data)
    summary_text = "\n".join(summary)
    assert "=== SDR-004 STATE DIVERGENCE AUDIT DISPLAY ===" in summary_text
    assert "sim_sdr_vis_test" in summary_text
    assert "TASK_MUTATION_OVERRIDE" in summary_text
    assert "RELATIONAL_LOOP_DETECTED" in summary_text


def test_receipt_verification_display():
    """Verify cryptographic receipt verification display output."""
    crc_data = {
        "attestation_provider": "Asymmetric",
        "key_pair_identity": "test_identity",
        "verification_status": "SIGNATURE_VERIFIED",
        "hash_chain_integrity": "INTEGRITY_PASSED",
        "receipt_chain": [{
            "receipt_id": "rec_01",
            "hash": "hash_val",
            "signer": "signer_val"
        }]
    }

    display = ReceiptVerificationDisplay()
    report = display.build_verification_display(crc_data)
    report_text = "\n".join(report)
    assert "=== CRYPTOGRAPHIC RECEIPT VERIFICATION ===" in report_text
    assert "SIGNATURE_VERIFIED" in report_text
    assert "rec_01" in report_text


def test_demonstrator_orchestration_and_export(tmp_path):
    """Verify end-to-end orchestrator and exporter behavior."""
    guard_file = tmp_path / "context_guard_evidence.json"
    demo_file = tmp_path / "demonstrator_evidence.json"

    # Create pre-existing guard file
    mock_guard = {
        "session_id": "session_demo_orch",
        "timestamp": "2026-08-03T13:00:00Z",
        "intake_details": {"modified_files": ["sage/core/spek.py"]},
        "protection_evaluation": {"status": "CLEAN_WORKSPACE", "severity": "LOW"},
        "decision_record": {
            "checkpoint_id": "chk_demo_orch",
            "decision_state": "AUTO_AUTHORIZED",
            "supervisor_id": "SYSTEM_AUTO",
            "comments": "Comments.",
            "action_taken": "COMMIT_APPROVED"
        }
    }
    with open(guard_file, "w", encoding="utf-8") as f:
        json.dump(mock_guard, f)

    demo = SAGEEnterpriseDemonstrator(
        context_guard_path=str(guard_file),
        output_path=str(demo_file)
    )

    evidence_pack = demo.run_demonstration()

    # Structural verification
    assert "demonstrator_run_id" in evidence_pack
    assert "timestamp" in evidence_pack
    assert "compiled_lineage_report" in evidence_pack
    assert "divergence_visibility" in evidence_pack
    assert "verification_status_report" in evidence_pack
    assert evidence_pack["boundary_integrity_verification"]["sage_runtime_untouched"] is True

    # Check file was written
    assert demo_file.exists()
    with open(demo_file, "r", encoding="utf-8") as f:
        loaded_demo = json.load(f)

    assert loaded_demo["demonstrator_run_id"] == evidence_pack["demonstrator_run_id"]
    assert len(loaded_demo["compiled_lineage_report"]) > 0
