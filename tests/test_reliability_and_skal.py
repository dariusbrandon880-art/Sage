"""Unit and integration tests for SAGE 2 ReliabilityIncidentTracker and SKAL Intake Foundation."""

from fastapi.testclient import TestClient
from sage.api import app
from sage.models import ConfidenceLevel
from sage.validation import ReliabilityIncidentTracker
from sage.acr.skal import (
    SKALIntakeManager,
    SKALValidationReport,
    SKALDeploymentEvent,
    SKALArchitectureDecision,
)


def test_reliability_incident_tracker_lifecycle(tmp_path):
    # Setup temporary Memory store
    from sage.memory import Memory

    memory_store = Memory(storage_path=str(tmp_path))
    tracker = ReliabilityIncidentTracker(memory_store)

    # 1. Record an incident
    incident_id = tracker.record_incident(
        incident_type="exception",
        description="Database connection timeout",
        metadata={"host": "localhost", "port": 5432},
    )
    assert incident_id is not None

    # Retrieve and verify
    obj = memory_store.retrieve(incident_id)
    assert obj is not None
    assert obj.object_type == "reliability_incident"
    assert obj.content["incident_type"] == "exception"
    assert obj.content["description"] == "Database connection timeout"
    assert obj.content["resolved"] is False
    assert "reliability" in obj.tags

    # 2. List incidents
    incidents = tracker.list_incidents()
    assert len(incidents) == 1
    assert incidents[0].id == incident_id

    unresolved = tracker.list_incidents(resolved=False)
    assert len(unresolved) == 1

    resolved = tracker.list_incidents(resolved=True)
    assert len(resolved) == 0

    # 3. Resolve incident
    success = tracker.resolve_incident(incident_id, "Reconnected with backoff strategy")
    assert success is True

    # Verify resolved state
    obj_after = memory_store.retrieve(incident_id)
    assert obj_after.content["resolved"] is True
    assert obj_after.content["resolution_details"] == "Reconnected with backoff strategy"
    assert obj_after.confidence == ConfidenceLevel.VALIDATED

    # List resolved again
    resolved_after = tracker.list_incidents(resolved=True)
    assert len(resolved_after) == 1
    assert resolved_after[0].id == incident_id


def test_skal_normalization_schemas():
    # 1. Validation Report with spaced keys
    report_data = {
        "report name": "SAGE Quality Audit",
        "status": "passed",
        "errors": [],
        "metadata": {"coverage": 95.5},
    }
    report = SKALValidationReport(**report_data)
    assert report.report_name == "SAGE Quality Audit"
    assert report.status == "passed"

    # 2. Deployment Event with snake_case and spaced keys mix
    event_data = {
        "event name": "Production Deploy",
        "environment": "prod",
        "status": "success",
        "metadata": {"version": "2.0.0"},
    }
    event = SKALDeploymentEvent(**event_data)
    assert event.event_name == "Production Deploy"
    assert event.environment == "prod"

    # 3. Architecture Decision
    decision_data = {
        "decision id": "ADR-100",
        "title": "Use Pydantic v2",
        "description": "Upgrade SAGE models to Pydantic v2 for performance",
        "metadata": {},
    }
    decision = SKALArchitectureDecision(**decision_data)
    assert decision.decision_id == "ADR-100"
    assert decision.title == "Use Pydantic v2"


def test_skal_intake_manager_processing(tmp_path):
    from sage.memory import Memory

    memory_store = Memory(storage_path=str(tmp_path))
    manager = SKALIntakeManager(memory_store)

    # Ingest a valid deployment event
    payload = {
        "payload_type": "deployment_event",
        "data": {
            "event name": "Staging Release",
            "environment": "staging",
            "status": "passed",
            "metadata": {"pipeline_id": 1234},
        },
    }

    result = manager.process_incoming_payload(payload)
    assert result["success"] is True
    assert result["payload_type"] == "deployment_event"
    memory_id = result["memory_id"]
    assert memory_id.startswith("skal_intake_")

    # Verify preserved evidence in memory ledger
    stored_obj = memory_store.retrieve(memory_id)
    assert stored_obj is not None
    assert stored_obj.object_type == "skal_deployment_event"
    assert stored_obj.content["event_name"] == "Staging Release"
    assert stored_obj.content["environment"] == "staging"


def test_reliability_and_skal_api_endpoints():
    client = TestClient(app)

    # 1. Test Incident Endpoint
    incident_payload = {
        "incident_type": "test",
        "description": "Pytest convergence failure",
        "metadata": {"failed_tests": ["test_acr_initialization"]},
    }
    response = client.post("/validation/incident", json=incident_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "incident_id" in res_data
    incident_id = res_data["incident_id"]

    # List incidents
    list_response = client.get("/validation/incidents?resolved=false")
    assert list_response.status_code == 200
    assert any(inc["id"] == incident_id for inc in list_response.json()["incidents"])

    # Resolve incident
    resolve_payload = {"resolution_details": "Re-run and verified convergence"}
    resolve_response = client.post(
        f"/validation/incident/{incident_id}/resolve", json=resolve_payload
    )
    assert resolve_response.status_code == 200

    # 2. Test SKAL Intake Endpoint
    skal_payload = {
        "payload_type": "validation_report",
        "data": {
            "report name": "Pre-flight Verification",
            "status": "failed",
            "errors": ["Missing credential.json"],
            "metadata": {"checked_at": "2026-07-23"},
        },
    }
    skal_response = client.post("/tools/skal/intake", json=skal_payload)
    assert skal_response.status_code == 200
    skal_res = skal_response.json()
    assert skal_res["success"] is True
    assert skal_res["payload_type"] == "validation_report"
    assert "memory_id" in skal_res
