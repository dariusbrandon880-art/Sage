"""ACR (Autonomous Continuity Runtime) Bridge - cross-session state continuity."""

from sage.acr.bridge import ACRBridge
from sage.acr.tool_bridge import (
    ToolPayload,
    TrustLevel,
    InvalidPayloadError,
    validate_tool_payload,
    classify_trust_level,
    get_repository_state,
    get_build_status,
    get_test_results,
    submit_validation_event,
)

__all__ = [
    "ACRBridge",
    "ToolPayload",
    "TrustLevel",
    "InvalidPayloadError",
    "validate_tool_payload",
    "classify_trust_level",
    "get_repository_state",
    "get_build_status",
    "get_test_results",
    "submit_validation_event",
]
