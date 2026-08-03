"""Unit test suite for SAGE Code-Modification Context Guard & Recovery Loop Foundation."""

import os
import json
import pytest
from sage.experimental.act.context_guard import (
    WorkspaceIntakeBridge,
    ProtectedChangeDetector,
    InteractiveApprovalCheckpoint,
    EvidenceReceiptGenerator,
    ContextGuardActivator
)


def test_context_guard_intake_bridge():
    """Verify workspace intake bridge ingests changes and catches invalid formats."""
    bridge = WorkspaceIntakeBridge(session_id="session_test_intake_01")
    assert bridge.session_id == "session_test_intake_01"

    # Ingest clean list of files
    payload = bridge.ingest_workspace_changes(["src/main.py", "docs/index.md"])
    assert payload["status"] == "INGESTED"
    assert "src/main.py" in payload["modified_files"]
    assert "docs/index.md" in payload["modified_files"]

    # Ingesting empty file paths should raise error
    with pytest.raises(ValueError, match="Modified file path cannot be empty"):
        bridge.ingest_workspace_changes([""])


def test_context_guard_protected_path_detection():
    """Verify detector flags protected namespaces correctly."""
    detector = ProtectedChangeDetector()

    # Clean workspace test
    clean_payload = {
        "modified_files": ["src/main.py", "docs/index.md", "README.md"]
    }
    report = detector.audit_changes(clean_payload)
    assert report["is_violation_found"] is False
    assert report["violations_found"] == 0
    assert report["severity"] == "LOW"
    assert report["status"] == "CLEAN_WORKSPACE"

    # Flagged workspace test
    violating_payload = {
        "modified_files": [
            "src/main.py",
            "sage/runtime/engine.py",
            "sage/core/spek.py",
            "./sage/acr/session/checkpoint.py"
        ]
    }
    violation_report = detector.audit_changes(violating_payload)
    assert violation_report["is_violation_found"] is True
    assert violation_report["violations_found"] == 3
    assert violation_report["severity"] == "HIGH"
    assert violation_report["status"] == "PROTECTION_VIOLATION_DETECTED"

    # Inspect violation details
    violation_paths = [v["file_path"] for v in violation_report["violations"]]
    assert "sage/runtime/engine.py" in violation_paths
    assert "sage/core/spek.py" in violation_paths
    assert "./sage/acr/session/checkpoint.py" in violation_paths


def test_context_guard_checkpoint_authorization():
    """Verify interactive checkpoint behavior with and without overrides."""
    checkpoint = InteractiveApprovalCheckpoint(checkpoint_id="chk_test_auth")

    # Clean report -> auto approval
    clean_report = {"is_violation_found": False}
    decision = checkpoint.request_approval(clean_report)
    assert decision["decision_state"] == "AUTO_AUTHORIZED"
    assert decision["action_taken"] == "COMMIT_APPROVED"

    # Violating report without override -> held
    violating_report = {"is_violation_found": True}
    decision_held = checkpoint.request_approval(violating_report)
    assert decision_held["decision_state"] == "HELD_FOR_HUMAN_APPROVAL"
    assert decision_held["action_taken"] == "EXECUTION_PAUSED"

    # Violating report with AUTHORIZED override -> approved
    override_authorized = {
        "decision": "AUTHORIZED",
        "supervisor_id": "human_supervisor_99",
        "comments": "Explicitly authorizing runtime patch."
    }
    decision_approved = checkpoint.request_approval(violating_report, override_authorized)
    assert decision_approved["decision_state"] == "AUTHORIZED"
    assert decision_approved["action_taken"] == "COMMIT_APPROVED"
    assert decision_approved["supervisor_id"] == "human_supervisor_99"

    # Violating report with REJECTED override -> rejected
    override_rejected = {
        "decision": "REJECTED",
        "supervisor_id": "human_supervisor_99",
        "comments": "Violation rejected."
    }
    decision_rejected = checkpoint.request_approval(violating_report, override_rejected)
    assert decision_rejected["decision_state"] == "REJECTED"
    assert decision_rejected["action_taken"] == "COMMIT_REJECTED"


def test_context_guard_evidence_generation(tmp_path):
    """Verify evidence receipt formatting and persistence."""
    evidence_file = tmp_path / "context_guard_evidence.json"
    generator = EvidenceReceiptGenerator(output_path=str(evidence_file))

    change_payload = {
        "session_id": "session_test_evidence",
        "modified_files": ["sage/core/spek.py"]
    }
    protection_report = {
        "status": "PROTECTION_VIOLATION_DETECTED",
        "violations_found": 1,
        "severity": "HIGH",
        "violations": [{
            "file_path": "sage/core/spek.py",
            "matched_prefix": "sage/core/",
            "severity": "CRITICAL"
        }]
    }
    decision_record = {
        "checkpoint_id": "chk_test_evidence",
        "decision_state": "AUTHORIZED",
        "supervisor_id": "human_supervisor_01",
        "comments": "Approved core change.",
        "action_taken": "COMMIT_APPROVED"
    }

    evidence_pack = generator.package_evidence(change_payload, protection_report, decision_record)

    # Validate structural fields
    assert evidence_pack["compliance_pack_id"] == "comp_s_guard_001"
    assert "receipt_id" in evidence_pack
    assert "timestamp" in evidence_pack
    assert evidence_pack["session_id"] == "session_test_evidence"
    assert "attestation" in evidence_pack
    assert "observed_results" in evidence_pack
    assert evidence_pack["boundary_integrity_verification"]["sage_runtime_untouched"] is True

    # Check file persistence
    assert evidence_file.exists()
    with open(evidence_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["receipt_id"] == evidence_pack["receipt_id"]
    assert loaded["decision_record"]["decision_state"] == "AUTHORIZED"


def test_context_guard_activator_pipeline(tmp_path):
    """Verify end-to-end activator flow."""
    evidence_file = tmp_path / "context_guard_evidence.json"
    activator = ContextGuardActivator(output_path=str(evidence_file))

    # Run clean loop
    clean_files = ["src/app.py", "tests/test_app.py"]
    receipt = activator.run_guard_loop(clean_files)

    assert receipt["protection_evaluation"]["status"] == "CLEAN_WORKSPACE"
    assert receipt["decision_record"]["decision_state"] == "AUTO_AUTHORIZED"
    assert receipt["observed_results"]["violations_intercepted"] == 0

    # Run violating loop with rejection override
    violating_files = ["sage/runtime/engine.py"]
    override = {
        "decision": "REJECTED",
        "supervisor_id": "supervisor_bob",
        "comments": "Do not touch production engine."
    }
    violating_receipt = activator.run_guard_loop(violating_files, override)

    assert violating_receipt["protection_evaluation"]["status"] == "PROTECTION_VIOLATION_DETECTED"
    assert violating_receipt["decision_record"]["decision_state"] == "REJECTED"
    assert violating_receipt["observed_results"]["violations_intercepted"] == 1
