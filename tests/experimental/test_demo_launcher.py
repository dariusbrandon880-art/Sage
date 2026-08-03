"""Unit test suite for SAGE Demonstration Launch Experience."""

import os
import json
from sage.experimental.act.demo_launcher import DemonstrationLauncher


def test_demonstration_launcher_config():
    """Verify that launcher loads the standardized configurations."""
    launcher = DemonstrationLauncher()
    config = launcher.load_standard_configuration()

    assert config["demo_name"] == "SAGE-ACT-PROD Launch Experience"
    assert "obj_audit_baseline" in config["active_objectives"]
    assert config["verification_mode"] == "strict"
    assert len(config["participants"]) == 3


def test_repeatable_flow_and_summary():
    """Verify end-to-end repeatable flow runs and summary terminal rendering."""
    launcher = DemonstrationLauncher()

    # 1. Test pristine baseline run
    outcome_pristine = launcher.execute_repeatable_flow(scenario="pristine_run")
    assert outcome_pristine["scenario"] == "pristine_run"
    assert outcome_pristine["human_checkpoint"]["gate_status"] == "BYPASS"

    # 2. Test divergence-resolution run
    outcome_div = launcher.execute_repeatable_flow(scenario="divergence_resolution")
    assert outcome_div["scenario"] == "divergence_resolution"
    assert outcome_div["divergence"]["conflicts_found"] == 1
    assert outcome_div["human_checkpoint"]["gate_status"] == "AUTHORIZED"

    # 3. Test summary output printing
    summary = launcher.render_summary_output(outcome_div)
    assert "SAGE ENTERPRISE DEMONSTRATION RUN COMPLETE" in summary
    assert "Session Identifier" in summary
    assert "Divergence Resolution" in summary or "divergence_resolution" in summary


def test_launcher_evidence_export(tmp_path):
    """Verify standard compliance evidence packaging and safe persistence."""
    evidence_file = tmp_path / "demo_launcher_evidence.json"
    launcher = DemonstrationLauncher(output_path=str(evidence_file))

    outcome = launcher.execute_repeatable_flow()

    # Check persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert "launcher_run_id" in loaded
    assert "timestamp" in loaded
    assert loaded["gate_verification_summary"]["gate_status"] == "AUTHORIZED"
    assert loaded["boundary_integrity_verification"]["sage_runtime_untouched"] is True

    # Check non-absolute results
    observed = loaded["observed_results"]
    assert "total_receipts_verified" in observed
    assert "launcher_run_duration_secs" in observed
    assert "estimated_baseline_reproducibility_percent" in observed
