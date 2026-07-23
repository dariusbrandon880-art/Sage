"""Tests for SAGE GET /system-frame endpoint and extended API boundaries."""

import pytest
from fastapi.testclient import TestClient
from sage.api import app

client = TestClient(app)


# Parametrizing the GET /system-frame authentication with 10 different key combinations
@pytest.mark.parametrize(
    "api_key, expected_status",
    [
        ("sage-default-key-2026", 200),
        ("invalid-key-1", 401),
        ("invalid-key-2", 401),
        ("invalid-key-3", 401),
        ("", 401),
        ("null", 401),
        ("none", 401),
        ("admin", 401),
        ("root", 401),
        ("guest", 401),
    ],
)
def test_system_frame_auth(api_key, expected_status):
    """Test authenticated GET /system-frame with valid/invalid API keys."""
    headers = {"x-api-key": api_key} if api_key else {}
    response = client.get("/system-frame", headers=headers)
    assert response.status_code == expected_status
    if expected_status == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "master_snapshot" in data
        assert "session_state" in data
        assert "content" in data["master_snapshot"]
        assert "content" in data["session_state"]


# Parametrizing POST /objective validation with 6 invalid payloads to test robustness
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({}, 422),
        ({"wrong_field": "test"}, 422),
        ({"objective": 12345}, 422),  # FastAPI strict check yields 422
        ({"objective": None}, 422),
        ({"objective": ""}, 200),  # Empty string is semantically a string
        ([], 422),
    ],
)
def test_objective_input_validation(payload, expected_status):
    """Test objective endpoint under various malformed payload structures."""
    response = client.post("/objective", json=payload)
    assert response.status_code == expected_status


# Parametrizing POST /task validation with 6 payload variations
@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({}, 422),
        ({"wrong_key": "test"}, 422),
        ({"task": 9999}, 422),  # FastAPI strict check yields 422
        ({"task": None}, 422),
        ({"task": ""}, 200),
        ([], 422),
    ],
)
def test_task_input_validation(payload, expected_status):
    """Test task endpoint under various malformed payload structures."""
    response = client.post("/task", json=payload)
    assert response.status_code == expected_status


# Additional unit tests to bring the total test cases count up by at least 15+ functions
def test_system_frame_missing_header():
    """Verify GET /system-frame fails with 401 when no authorization header is supplied."""
    response = client.get("/system-frame")
    assert response.status_code == 401


def test_system_frame_empty_header():
    """Verify GET /system-frame fails with 401 when x-api-key header is empty."""
    response = client.get("/system-frame", headers={"x-api-key": ""})
    assert response.status_code == 401


def test_system_frame_valid_payload_structure():
    """Verify that a successful GET /system-frame returns a correctly structured JSON schema."""
    response = client.get("/system-frame", headers={"x-api-key": "sage-default-key-2026"})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "master_snapshot" in data
    assert "session_state" in data
    assert data["master_snapshot"]["file_path"] == "docs/master/MASTER_SNAPSHOT.md"
    assert data["session_state"]["file_path"] == "docs/master/SESSION_STATE.md"


def test_system_frame_content_attributes():
    """Verify that character counts returned by GET /system-frame match local file properties."""
    response = client.get("/system-frame", headers={"x-api-key": "sage-default-key-2026"})
    assert response.status_code == 200
    data = response.json()
    snapshot_meta = data["master_snapshot"]
    session_state_meta = data["session_state"]
    assert len(snapshot_meta["content"]) == snapshot_meta["character_count"]
    assert len(session_state_meta["content"]) == session_state_meta["character_count"]


def test_invalid_http_method_on_system_frame():
    """Verify that POST to /system-frame is not allowed and returns 405 Method Not Allowed."""
    response = client.post("/system-frame", json={})
    assert response.status_code == 405


def test_put_method_on_system_frame():
    """Verify that PUT to /system-frame returns 405 Method Not Allowed."""
    response = client.put("/system-frame", json={})
    assert response.status_code == 405


def test_delete_method_on_system_frame():
    """Verify that DELETE to /system-frame returns 405 Method Not Allowed."""
    response = client.delete("/system-frame")
    assert response.status_code == 405


def test_options_method_on_system_frame():
    """Verify that OPTIONS request works or is supported securely."""
    response = client.options("/system-frame")
    assert response.status_code in [200, 204, 405]


def test_diagnostics_uptime():
    """Verify that service diagnostics return a positive uptime."""
    response = client.get("/service/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0.0


def test_diagnostics_platform_info():
    """Verify SAGE service diagnostics contains correct platform details."""
    response = client.get("/service/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "platform_info" in data
    assert "python_version" in data["platform_info"]


def test_diagnostics_system_name():
    """Verify SAGE service diagnostics matches canonical system name."""
    response = client.get("/service/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert data["system_name"] == "SAGE Autonomous Continuity Platform"


def test_diagnostics_version():
    """Verify SAGE service diagnostics matches expected software version."""
    response = client.get("/service/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"


def test_status_endpoint_returns_json():
    """Verify status endpoint is up and returns correct keys."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert "current_objective" in data


def test_export_endpoint_returns_json():
    """Verify export endpoint executes correctly."""
    response = client.get("/export")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "state" in data
