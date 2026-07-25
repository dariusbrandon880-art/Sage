"""Unit tests verifying canonical SAGE ACR/CIV schema contracts and API error-mapping."""

import pytest
from pydantic import ValidationError
from datetime import datetime

from sage.acr.models import (
    CIVValidationPassEvent,
    CIVValidationFailEvent,
    map_civ_error_to_response
)


def test_validation_pass_event_valid_instantiation():
    """Verify that a valid CIVValidationPassEvent instantiates and validates cleanly."""
    event = CIVValidationPassEvent(
        session_id="session_123",
        transition_from="S0",
        transition_to="S1",
        evidence_hash="hash_abc_123"
    )

    assert event.event_type == "VALIDATION_PASS"
    assert isinstance(event.timestamp, datetime)
    assert event.session_id == "session_123"
    assert event.transition_from == "S0"
    assert event.transition_to == "S1"
    assert event.evidence_hash == "hash_abc_123"
    assert event.metadata == {}


def test_validation_pass_event_missing_fields_rejection():
    """Verify that omitting required fields on CIVValidationPassEvent raises a ValidationError."""
    with pytest.raises(ValidationError):
        CIVValidationPassEvent(
            session_id="session_123"
            # missing transition_from, transition_to, and evidence_hash
        )


def test_validation_fail_event_valid_instantiation():
    """Verify that a valid CIVValidationFailEvent instantiates and validates cleanly."""
    event = CIVValidationFailEvent(
        session_id="session_123",
        error_code="CIV-ERR-MUT-003",
        error_message="Identity mutation was blocked",
        attempted_from="S0",
        attempted_to="S1",
        failed_fields=["identity"]
    )

    assert event.event_type == "VALIDATION_FAIL"
    assert isinstance(event.timestamp, datetime)
    assert event.session_id == "session_123"
    assert event.error_code == "CIV-ERR-MUT-003"
    assert event.error_message == "Identity mutation was blocked"
    assert event.attempted_from == "S0"
    assert event.attempted_to == "S1"
    assert event.failed_fields == ["identity"]


def test_validation_fail_event_missing_fields_rejection():
    """Verify that omitting required fields on CIVValidationFailEvent raises a ValidationError."""
    with pytest.raises(ValidationError):
        CIVValidationFailEvent(
            session_id="session_123"
            # missing error_code, error_message, attempted_from, and attempted_to
        )


def test_map_civ_error_to_response_valid_codes():
    """Verify that all canonical CIV-ERR-* codes map correctly into standard structured API responses."""
    test_cases = [
        ("CIV-ERR-MUT-003", 409, "Identity Mutation Violation"),
        ("CIV-ERR-AUTH-001", 401, "Authority Signature Mismatch"),
        ("CIV-ERR-SCHM-002", 422, "Malformed Structure"),
        ("CIV-ERR-SCHM-005", 400, "Missing Schema Field"),
        ("CIV-ERR-EXT-004", 400, "Ambiguous Payload Specification")
    ]

    for code, expected_status, expected_title in test_cases:
        response = map_civ_error_to_response(
            error_code=code,
            details="Custom failure detail message",
            failed_fields=["field_x"]
        )

        assert response["status_code"] == expected_status
        assert response["error"]["code"] == code
        assert response["error"]["title"] == expected_title
        assert response["error"]["message"] == "Custom failure detail message"
        assert response["error"]["failed_fields"] == ["field_x"]
        assert "timestamp" in response["error"]


def test_map_civ_error_to_response_unspecified_fallback_code():
    """Verify that an unrecognized error code safely falls back to internal server error response."""
    response = map_civ_error_to_response(error_code="CIV-ERR-UNKNOWN-999")

    assert response["status_code"] == 500
    assert response["error"]["code"] == "CIV-ERR-UNKNOWN-999"
    assert response["error"]["title"] == "Internal Connection Error"
    assert "validation failure" in response["error"]["message"]
