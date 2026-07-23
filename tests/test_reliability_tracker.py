"""Unit and Integration tests for SAGE 2 Reliability and Evolution Tracking."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from sage.api import app
from sage.runtime import SageRuntime
from sage.models import ReliabilityIncident, ReliabilityIncidentType
from sage.validation import ReliabilityIncidentTracker

client = TestClient(app)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_reliability_incident_tracker_operations(temp_workspace):
    """Test standard CRUD operations for ReliabilityIncidentTracker natively."""
    runtime = SageRuntime(str(temp_workspace))
    tracker = ReliabilityIncidentTracker(runtime.memory)

    # 1. Create and record an incident
    incident = ReliabilityIncident(
        incident_type=ReliabilityIncidentType.EXCEPTION,
        source="sage/api.py",
        affected_component="MemoryStore",
        reproduction={"stack_trace": "ValueError: MemoryObject not found"},
    )
    incident_id = tracker.record_incident(incident)
    assert incident_id == incident.id

    # 2. Retrieve the incident
    retrieved = tracker.retrieve_incident(incident_id)
    assert retrieved is not None
    assert retrieved.incident_type == ReliabilityIncidentType.EXCEPTION
    assert retrieved.status == "PENDING"

    # 3. List incidents
    incidents = tracker.list_incidents()
    assert len(incidents) == 1
    assert incidents[0].id == incident_id

    # 4. Resolve the incident
    success = tracker.resolve_incident(
        incident_id, status="RESOLVED", validation_evidence=["test_evidence_id_001"]
    )
    assert success is True

    # Confirm updates are persisted
    updated = tracker.retrieve_incident(incident_id)
    assert updated.status == "RESOLVED"
    assert "test_evidence_id_001" in updated.validation_evidence


def test_api_reliability_incident_endpoints(temp_workspace):
    """Test structured reliability incident REST endpoints via FastAPI Client."""
    # 1. Record Incident
    payload = {
        "incident_type": "security_vulnerability",
        "source": "scripts/production_check.py",
        "affected_component": "FastAPI Header Auth",
        "reproduction": {"issue": "SAGE_API_KEYS using default value"},
    }
    response = client.post("/validation/incident", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert data["status"] == "recorded"
    incident_id = data["incident_id"]

    # 2. List Incidents
    response = client.get("/validation/incidents")
    assert response.status_code == 200
    list_data = response.json()
    assert list_data["count"] >= 1
    assert any(inc["id"] == incident_id for inc in list_data["incidents"])

    # 3. Resolve Incident
    resolve_payload = {
        "status": "VALIDATED",
        "validation_evidence": ["evidence_id_999"],
    }
    response = client.post(f"/validation/incident/{incident_id}/resolve", json=resolve_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_api_reliability_incident_invalid_type():
    """Verify that recording an incident with an invalid type fails with 400."""
    payload = {
        "incident_type": "invalid_type_here",
        "source": "tests",
        "affected_component": "Core",
    }
    response = client.post("/validation/incident", json=payload)
    assert response.status_code == 400
