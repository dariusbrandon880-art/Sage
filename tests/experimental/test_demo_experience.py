"""Unit test suite for SAGE Enterprise Demonstration Experience Integration."""

import os
import json
import pytest
from sage.experimental.act.demo_experience import SAGEExperienceCoordinator


def test_sage_experience_coordinator_clean(tmp_path):
    """Verify integrated demonstration experience on a clean workspace configuration."""
    evidence_file = tmp_path / "demo_experience_evidence.json"
    coordinator = SAGEExperienceCoordinator(output_path=str(evidence_file))

    files = ["src/utils.py"]
    receipt = coordinator.run_experience(files)

    # Invariants
    assert receipt["experience_run_id"].startswith("demo_exp_")
    assert receipt["integrated_lineage"]["user_action"]["files_count"] == 1
    assert receipt["integrated_lineage"]["spek_evaluation"]["status"] == "CLEAN_WORKSPACE"
    assert receipt["integrated_lineage"]["hdg_checkpoint"]["decision_state"] == "AUTO_AUTHORIZED"
    assert receipt["integrated_lineage"]["sdr_divergence"]["simulation_id"] == "sim_sdr004_dem_01"
    assert receipt["integrated_lineage"]["crc_verification"]["verification_status"] == "SIGNATURE_VERIFIED"
    assert receipt["observed_results"]["has_violations_rendered"] == 0

    # Dashboard assertions
    assert len(receipt["demonstration_dashboard"]) > 0
    dashboard_text = "\n".join(receipt["demonstration_dashboard"])
    assert "SAGE ENTERPRISE DEMONSTRATION INTEGRATED EXPERIENCE COCONSOLE" in dashboard_text
    assert "=== SAGE CHRONOLOGICAL AUDIT LINEAGE ===" in dashboard_text
    assert "=== SDR-004 STATE DIVERGENCE AUDIT DISPLAY ===" in dashboard_text
    assert "=== CRYPTOGRAPHIC RECEIPT VERIFICATION ===" in dashboard_text

    # File persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["experience_run_id"] == receipt["experience_run_id"]


def test_sage_experience_coordinator_violating_with_override(tmp_path):
    """Verify integrated experience behaves correctly when violations are overridden."""
    evidence_file = tmp_path / "demo_experience_evidence.json"
    coordinator = SAGEExperienceCoordinator(output_path=str(evidence_file))

    files = ["sage/runtime/engine.py"]
    override = {
        "decision": "AUTHORIZED",
        "supervisor_id": "human_supervisor_01",
        "comments": "Approved."
    }
    receipt = coordinator.run_experience(files, supervisor_override=override)

    assert receipt["integrated_lineage"]["spek_evaluation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert receipt["integrated_lineage"]["spek_evaluation"]["violations_found"] == 1
    assert receipt["integrated_lineage"]["hdg_checkpoint"]["decision_state"] == "AUTHORIZED"
    assert receipt["observed_results"]["has_violations_rendered"] == 1
