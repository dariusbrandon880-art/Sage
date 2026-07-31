"""SAGE Experimental Resilient Fallback Tests."""

import os
import json
import pytest
import shutil
from sage.experimental.act.fallbacks import ResilientIntegrationBridge


@pytest.fixture
def temp_credentials_dir():
    """Fixture providing a temporary directory for credential mocks."""
    test_dir = "sage_data/test_credentials"
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_credentials_missing_degraded(temp_credentials_dir):
    """Verify that a missing credentials file returns a degraded sync status gracefully."""
    bridge = ResilientIntegrationBridge(fallback_enabled=True)
    missing_path = os.path.join(temp_credentials_dir, "missing_creds.json")

    diagnostics = bridge.validate_credentials(missing_path)

    assert diagnostics["status"] == "DEGRADED"
    assert "not found" in diagnostics["reason"]
    assert diagnostics["sync_enabled"] is False
    assert diagnostics["mock_mode"] is True


def test_credentials_invalid_path():
    """Verify that passing an empty/None path is handled gracefully."""
    bridge = ResilientIntegrationBridge()
    diagnostics = bridge.validate_credentials("")
    assert diagnostics["status"] == "DEGRADED"
    assert diagnostics["sync_enabled"] is False


def test_credentials_corrupted_degraded(temp_credentials_dir):
    """Verify that a corrupted JSON credentials file is caught and degraded gracefully."""
    bridge = ResilientIntegrationBridge()
    corrupt_path = os.path.join(temp_credentials_dir, "corrupt_creds.json")

    with open(corrupt_path, "w", encoding="utf-8") as f:
        f.write("{corrupted JSON content")

    diagnostics = bridge.validate_credentials(corrupt_path)

    assert diagnostics["status"] == "DEGRADED"
    assert "credentials file" in diagnostics["reason"]
    assert diagnostics["sync_enabled"] is False


def test_credentials_valid_healthy(temp_credentials_dir):
    """Verify that a valid credentials file returns a healthy sync status."""
    bridge = ResilientIntegrationBridge()
    valid_path = os.path.join(temp_credentials_dir, "valid_creds.json")

    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump({"installed": {"client_id": "dummy_client"}}, f)

    diagnostics = bridge.validate_credentials(valid_path)

    assert diagnostics["status"] == "HEALTHY"
    assert diagnostics["sync_enabled"] is True
    assert diagnostics["mock_mode"] is False


def test_execute_sync_fallback_active(temp_credentials_dir):
    """Verify that sync execution gracefully utilizes mock fallback data when missing credentials."""
    bridge = ResilientIntegrationBridge(fallback_enabled=True)
    missing_path = os.path.join(temp_credentials_dir, "missing_creds.json")

    fallback_payload = {"synchronized_events_count": 0, "mock_rehydration": True}

    def failing_action():
        raise Exception("Should not be called")

    response = bridge.execute_sync_safely(
        credentials_path=missing_path,
        sync_action=failing_action,
        fallback_payload=fallback_payload,
    )

    assert response["status"] == "FALLBACK_ACTIVE"
    assert response["result"] == fallback_payload
    assert response["diagnostics"]["sync_enabled"] is False


def test_execute_sync_success_path(temp_credentials_dir):
    """Verify that sync execution is successful when credentials exist and action succeeds."""
    bridge = ResilientIntegrationBridge()
    valid_path = os.path.join(temp_credentials_dir, "valid_creds.json")

    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump({"client_id": "123"}, f)

    def success_action():
        return {"live_sync": True, "count": 100}

    fallback_payload = {"live_sync": False}

    response = bridge.execute_sync_safely(
        credentials_path=valid_path,
        sync_action=success_action,
        fallback_payload=fallback_payload,
    )

    assert response["status"] == "SUCCESS"
    assert response["result"]["live_sync"] is True
    assert response["result"]["count"] == 100
    assert response["diagnostics"]["sync_enabled"] is True


def test_execute_sync_live_failure_fallback_active(temp_credentials_dir):
    """Verify that live execution failures trigger graceful fallbacks when enabled."""
    bridge = ResilientIntegrationBridge(fallback_enabled=True)
    valid_path = os.path.join(temp_credentials_dir, "valid_creds.json")

    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump({"client_id": "123"}, f)

    def crashing_action():
        raise RuntimeError("API Timeout / Connection Lost")

    fallback_payload = {"live_sync": False, "cached_data": True}

    response = bridge.execute_sync_safely(
        credentials_path=valid_path,
        sync_action=crashing_action,
        fallback_payload=fallback_payload,
    )

    assert response["status"] == "FALLBACK_ACTIVE"
    assert response["result"] == fallback_payload
    assert response["diagnostics"]["status"] == "DEGRADED"


def test_execute_sync_fallback_disabled_throws(temp_credentials_dir):
    """Verify that disabling fallback throws errors when action fails or credentials are missing."""
    bridge = ResilientIntegrationBridge(fallback_enabled=False)
    missing_path = os.path.join(temp_credentials_dir, "missing_creds.json")

    with pytest.raises(FileNotFoundError, match="Google Workspace credentials file not found"):
        bridge.execute_sync_safely(missing_path, lambda: None, {})
