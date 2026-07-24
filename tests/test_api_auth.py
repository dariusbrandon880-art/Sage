"""Tests for SAGE API global authentication boundaries."""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from sage.api import app


def test_api_no_auth_by_default():
    """By default, when SAGE_REQUIRE_AUTH is not set (or is false), endpoints are fully accessible."""
    with patch.dict(os.environ, {"SAGE_REQUIRE_AUTH": "false"}), TestClient(app) as client:
        response = client.get("/status")
        assert response.status_code == 200


def test_api_auth_enforced_unauthorized():
    """When SAGE_REQUIRE_AUTH is set to true, operational endpoints must block unauthorized requests."""
    with patch.dict(os.environ, {"SAGE_REQUIRE_AUTH": "true"}), TestClient(app) as client:
        # Operational endpoint should be blocked
        response = client.get("/status")
        assert response.status_code == 401
        assert "Unauthorized" in response.json()["detail"]


def test_api_auth_enforced_authorized_valid_key():
    """When SAGE_REQUIRE_AUTH is set to true, requests with a valid x-api-key header are allowed."""
    with patch.dict(os.environ, {"SAGE_REQUIRE_AUTH": "true", "SAGE_API_KEYS": "valid-secret-key"}):
        with TestClient(app) as client:
            # Operational endpoint with valid key should pass
            response = client.get("/status", headers={"x-api-key": "valid-secret-key"})
            assert response.status_code == 200


def test_api_auth_enforced_unauthorized_invalid_key():
    """When SAGE_REQUIRE_AUTH is set to true, requests with an invalid x-api-key header are blocked."""
    with patch.dict(os.environ, {"SAGE_REQUIRE_AUTH": "true", "SAGE_API_KEYS": "valid-secret-key"}):
        with TestClient(app) as client:
            # Operational endpoint with invalid key should fail
            response = client.get("/status", headers={"x-api-key": "invalid-secret-key"})
            assert response.status_code == 401


def test_api_auth_bypassed_for_public_endpoints():
    """Even when SAGE_REQUIRE_AUTH is true, health and root paths remain publicly accessible."""
    with patch.dict(os.environ, {"SAGE_REQUIRE_AUTH": "true"}), TestClient(app) as client:
        # Root path is public
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "SAGE Runtime online"

        # Health path is public
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
