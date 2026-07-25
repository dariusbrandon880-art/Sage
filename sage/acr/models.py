"""Canonical ACR/CIV Event Contract Schemas and Error Mapping for SAGE.

This module defines the structured Pydantic schemas representing validation outcomes
and handles formatting CIV-ERR-* failures into standard structured API responses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class CIVValidationPassEvent(BaseModel):
    """Event representation of a successfully validated state transition (VALIDATION_PASS)."""

    event_type: str = Field("VALIDATION_PASS", description="Canonical event status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of validation pass"
    )
    session_id: str = Field(..., description="Active session ID associated with transition")
    transition_from: str = Field(..., description="Pre-transition state (e.g. S0)")
    transition_to: str = Field(..., description="Post-transition state (e.g. S1)")
    evidence_hash: str = Field(..., description="SHA-256 hash verifying transition payload integrity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context parameters")


class CIVValidationFailEvent(BaseModel):
    """Event representation of a rejected state transition (VALIDATION_FAIL)."""

    event_type: str = Field("VALIDATION_FAIL", description="Canonical event status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of validation failure"
    )
    session_id: str = Field(..., description="Active session ID associated with transition")
    error_code: str = Field(..., description="Canonical SAGE-CIV error code (e.g. CIV-ERR-MUT-003)")
    error_message: str = Field(..., description="Human-readable description of validation failure")
    attempted_from: str = Field(..., description="Attempted pre-transition state")
    attempted_to: str = Field(..., description="Attempted post-transition state")
    failed_fields: List[str] = Field(default_factory=list, description="Fields that failed validation constraints")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional failure diagnostics")


# Canonical CIV error registry and API structure mapping
CIV_ERROR_REGISTRY = {
    "CIV-ERR-MUT-003": {
        "status_code": 409,
        "title": "Identity Mutation Violation",
        "description": "Attempt to mutate node identity or session ownership during transaction is forbidden."
    },
    "CIV-ERR-AUTH-001": {
        "status_code": 401,
        "title": "Authority Signature Mismatch",
        "description": "Provided authorization or cryptographic signature does not match registered authority."
    },
    "CIV-ERR-SCHM-002": {
        "status_code": 422,
        "title": "Malformed Structure",
        "description": "The payload structure is malformed, invalid, or violates strict Pydantic requirements."
    },
    "CIV-ERR-SCHM-005": {
        "status_code": 400,
        "title": "Missing Schema Field",
        "description": "Mandatory fields required for executing a valid state transition are missing."
    },
    "CIV-ERR-EXT-004": {
        "status_code": 400,
        "title": "Ambiguous Payload Specification",
        "description": "Payload contains logically conflicting signals or ambiguous execution paths."
    }
}


def map_civ_error_to_response(error_code: str, details: str | None = None, failed_fields: List[str] | None = None) -> Dict[str, Any]:
    """Map a canonical CIV-ERR-* failure into a structured API response format.

    Args:
        error_code: The CIV error code.
        details: Optional detailed error message or context.
        failed_fields: Optional list of fields causing the validation failure.

    Returns:
        A dictionary containing the structured API error response.
    """
    config = CIV_ERROR_REGISTRY.get(error_code, {
        "status_code": 500,
        "title": "Internal Connection Error",
        "description": "An unspecified state transition validation failure occurred."
    })

    return {
        "status_code": config["status_code"],
        "error": {
            "code": error_code,
            "title": config["title"],
            "message": details or config["description"],
            "failed_fields": failed_fields or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
