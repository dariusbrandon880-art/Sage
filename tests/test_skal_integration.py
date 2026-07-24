"""Unit and integration tests for SKAL-Validation-Promotion pipeline and C.11 Continuity hooks."""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sage.api import app
from sage.models import ConfidenceLevel
from sage.acr.skal import SKALIntakeManager
from sage.acr.continuity_integration import (
    IdentityDriftMonitor,
    StateCalibrationSync,
    AdaptiveDecay,
    StateReconciliation,
    ContinuitySecurity,
)


@pytest.fixture
def clean_intake_manager(tmp_path):
    from sage.memory import Memory
    from sage.runtime import SageRuntime

    memory_store = Memory(storage_path=str(tmp_path))
    runtime = SageRuntime(workspace_path=str(tmp_path))
    return SKALIntakeManager(memory_store, runtime)


def test_skal_validation_report_promotion(clean_intake_manager):
    # 1. Successful Intake
    payload = {
        "payload_type": "validation_report",
        "data": {
            "report name": "Audit passed",
            "status": "passed",
            "errors": [],
            "metadata": {"coverage": 98.2},
        },
    }
    intake_res = clean_intake_manager.process_incoming_payload(payload)
    assert intake_res["success"] is True
    memory_id = intake_res["memory_id"]

    # 2. Promotion - Rejected Bypass (missing signature)
    promo_reject = clean_intake_manager.promote_skal_record(memory_id=memory_id)
    assert promo_reject["success"] is False
    assert "Authorized signature is required" in promo_reject["error"]

    # 3. Promotion - Successful
    promo_success = clean_intake_manager.promote_skal_record(
        memory_id=memory_id, authorizer_signature="AUTHORIZED_SIGN_SAGE2"
    )
    assert promo_success["success"] is True
    assert promo_success["status"] == "promoted"
    assert promo_success["archive_id"].startswith("archive_skal_")

    # Confirm confidence updated in memory
    stored_obj = clean_intake_manager.memory.retrieve(memory_id)
    assert stored_obj.confidence == ConfidenceLevel.VALIDATED


def test_skal_validation_report_failed_status(clean_intake_manager):
    # Intake of a failed report
    payload = {
        "payload_type": "validation_report",
        "data": {
            "report name": "Audit failed",
            "status": "failed",
            "errors": ["Missing tests"],
            "metadata": {},
        },
    }
    intake_res = clean_intake_manager.process_incoming_payload(payload)
    memory_id = intake_res["memory_id"]

    # Promotion - Reject due to failed status
    promo_res = clean_intake_manager.promote_skal_record(
        memory_id=memory_id, authorizer_signature="AUTHORIZED_SIGN_SAGE2"
    )
    assert promo_res["success"] is False
    assert "status is 'failed'" in promo_res["error"]


def test_skal_architecture_decision_promotion(clean_intake_manager):
    # 1. Intake of decision without evidence in metadata
    payload_no_lineage = {
        "payload_type": "architecture_decision",
        "data": {
            "decision id": "ADR-101",
            "title": "Use Local Storage",
            "description": "Store json files locally",
            "metadata": {},  # Empty evidence lineage!
        },
    }
    intake_no_lineage = clean_intake_manager.process_incoming_payload(payload_no_lineage)
    memory_id_no = intake_no_lineage["memory_id"]

    # Promotion - Reject due to missing lineage
    promo_reject = clean_intake_manager.promote_skal_record(
        memory_id=memory_id_no, authorizer_signature="AUTHORIZED_SIGN_SAGE2"
    )
    assert promo_reject["success"] is False
    assert "preserve lineage to source evidence" in promo_reject["error"]

    # 2. Intake of decision WITH evidence lineage
    payload_valid = {
        "payload_type": "architecture_decision",
        "data": {
            "decision id": "ADR-102",
            "title": "Use SQLite Storage",
            "description": "Store records in sqlite databases",
            "metadata": {"evidence": ["skal_intake_abc123"]},
        },
    }
    intake_valid = clean_intake_manager.process_incoming_payload(payload_valid)
    memory_id_val = intake_valid["memory_id"]

    # Promotion - Successful
    promo_success = clean_intake_manager.promote_skal_record(
        memory_id=memory_id_val, authorizer_signature="AUTHORIZED_SIGN_SAGE2"
    )
    assert promo_success["success"] is True
    assert promo_success["status"] == "promoted"


def test_skal_deployment_event_state_routing(clean_intake_manager):
    # Setup active runtime session
    session_id = clean_intake_manager.runtime.set_objective("Sprint 4 Implementation")

    payload = {
        "payload_type": "deployment_event",
        "data": {
            "event name": "Production Deploy",
            "environment": "prod",
            "status": "success",
            "metadata": {"pipeline_id": 9999},
        },
    }

    intake_res = clean_intake_manager.process_incoming_payload(payload)
    memory_id = intake_res["memory_id"]

    # Promotion - Deployment event updates operational state only, bypassing Master Archive
    promo_res = clean_intake_manager.promote_skal_record(memory_id=memory_id)
    assert promo_res["success"] is True
    assert promo_res["status"] == "operational_updated"
    assert promo_res["session_id"] == session_id

    # Verify session state metadata was successfully updated with deployment event
    session_state = clean_intake_manager.runtime.session_manager.retrieve_session(session_id)
    assert session_state.metadata["deployment_status"] == "success"
    assert session_state.metadata["last_deployment_event"]["environment"] == "prod"


def test_c11_continuity_integration_hooks():
    # 1. Identity Drift Monitor
    monitor = IdentityDriftMonitor()
    drift_res = monitor.analyze_schema_drift(["skal_schema", "acr_schema"])
    assert drift_res["status"] == "synchronized"
    assert drift_res["drift_score"] == 1.0

    # 2. State Calibration Sync
    sync = StateCalibrationSync(None)
    calibration = sync.calibrate_embeddings("context_id_1")
    assert calibration["status"] == "calibrated"

    # 3. Adaptive Decay
    decay = AdaptiveDecay(half_life_hours=24.0)
    created_at = datetime.now(timezone.utc) - timedelta(hours=24.0)
    decayed_score = decay.calculate_importance_decay(created_at, 1.0)
    assert decayed_score == 0.5  # Exactly 1 half-life

    # 4. State Reconciliation
    recon = StateReconciliation(None)
    recon_res = recon.reconcile_session_trees("sess_A", "sess_B")
    assert recon_res["reconciliation_status"] == "merged"

    # 5. Continuity Security
    sec = ContinuitySecurity()
    assert sec.verify_token_chain("valid_token_string_12345", "node_A") is True
    assert sec.verify_token_chain("", "node_A") is False


def test_skal_promotion_api_endpoint():
    client = TestClient(app)

    # 1. Ingest validation report via API
    intake_payload = {
        "payload_type": "validation_report",
        "data": {
            "report name": "Pre-flight Verification",
            "status": "passed",
            "errors": [],
            "metadata": {},
        },
    }
    intake_response = client.post("/tools/skal/intake", json=intake_payload)
    assert intake_response.status_code == 200
    memory_id = intake_response.json()["memory_id"]

    # 2. Promote via API (with validation authority / signature)
    promo_payload = {"memory_id": memory_id, "authorizer_signature": "AUTHORIZED_SIGN_SAGE2"}
    promo_response = client.post("/tools/skal/promote", json=promo_payload)
    assert promo_response.status_code == 200
    assert promo_response.json()["success"] is True
    assert promo_response.json()["status"] == "promoted"
