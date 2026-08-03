"""Unit test suite for SAGE-ACT-PROD Demonstrator Foundation."""

import os
import json
import pytest
from sage.experimental.act.act_prod_demonstrator import (
    DemonstratorAPI,
    AuditLineageVisualizer,
    DemonstratorEvidenceExporter
)


def test_demonstrator_api_endpoints():
    """Verify that DemonstratorAPI serves valid schema payloads and tracks activity."""
    api = DemonstratorAPI("session_test_act_prod")

    # 1. Test Lineage Endpoint
    lineage = api.get_lineage()
    assert lineage["session_id"] == "session_test_act_prod"
    assert "mapped_tasks" in lineage
    assert lineage["verification_status"] == "LINEAGE_VALIDATED"

    # 2. Test Divergence Endpoint
    divergence = api.get_divergence()
    assert divergence["session_id"] == "session_test_act_prod"
    assert divergence["conflicts_found"] == 1
    assert divergence["conflicts"][0]["conflict_type"] == "TASK_MUTATION_OVERRIDE"

    # 3. Test Checkpoints Endpoint
    checkpoints = api.get_checkpoints()
    assert checkpoints["session_id"] == "session_test_act_prod"
    assert checkpoints["active_checkpoints"][0]["checkpoint_id"] == "chk_act_prod_01"

    # 4. Test Verify Endpoint
    verify = api.get_verify()
    assert verify["session_id"] == "session_test_act_prod"
    assert verify["chain_integrity"] == "SECURE_PASSED"
    assert verify["non_repudiation_status"] == "VERIFIED_INDISPUTABLE"

    # Verify tracked activity
    assert len(api.endpoints_accessed) == 4
    assert "/api/demonstrator/lineage" in api.endpoints_accessed
    assert "/api/demonstrator/verify" in api.endpoints_accessed


def test_audit_lineage_visualizer(tmp_path):
    """Verify visualizer loads template and injects dynamic data correctly."""
    # Write a test template
    test_template = tmp_path / "test_visualizer.html"
    with open(test_template, "w", encoding="utf-8") as f:
        f.write("<html><body>{{MOCK_SESSION_DATA}}</body></html>")

    visualizer = AuditLineageVisualizer(template_path=str(test_template))

    # Render with override data
    override_data = {"test_key": "active_trace_payload"}
    rendered = visualizer.render_html_page(mock_data_override=override_data)

    assert "active_trace_payload" in rendered
    assert "test_key" in rendered

    # Nonexistent template path should raise FileNotFoundError
    bad_visualizer = AuditLineageVisualizer(template_path="bad_path.html")
    with pytest.raises(FileNotFoundError):
        bad_visualizer.render_html_page()


def test_demonstrator_evidence_exporter(tmp_path):
    """Verify exporter packages activity and saves compliant compliance JSON."""
    output_file = tmp_path / "act_prod_demonstrator_run.json"
    exporter = DemonstratorEvidenceExporter(output_path=str(output_file))

    api_activity = ["/api/demonstrator/lineage", "/api/demonstrator/verify"]
    evidence = exporter.export_demonstrator_evidence(
        session_id="session_test_export",
        api_activity=api_activity,
        gate_state="AUTHORIZED"
    )

    # Check structural correctness
    assert "demonstrator_run_id" in evidence
    assert "timestamp" in evidence
    assert evidence["endpoints_accessed"] == api_activity
    assert evidence["simulated_gate_state"] == "AUTHORIZED"
    assert evidence["validation_summary"]["schema_compliance"] == "PASSED"
    assert evidence["boundary_integrity_verification"]["sage_runtime_untouched"] is True

    # Non-absolute metrics language verification
    observed = evidence["observed_results"]
    assert "visualizer_load_speed_secs" in observed
    assert "verification_latency_ms" in observed
    assert "demonstrator_resolution_success_rate_percent" in observed

    # Check persistence
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["demonstrator_run_id"] == evidence["demonstrator_run_id"]
