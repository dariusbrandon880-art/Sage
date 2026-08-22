"""Runtime engine and intelligence layers for SAGE autonomous operations.

Implements the SAGE Runtime Integrity Layer (SRIL) with the invariant sage.runtime:app
export boundary using module-level __getattr__ to lazy-load the FastAPI application from
sage.api to avoid circular imports during initialization.
"""

from typing import Any

from sage.runtime.capability_report import discover_capabilities, generate_capability_report
from sage.runtime.diagnostics import (
    InitializationManager,
    generate_diagnostic_report,
    generate_system_status_report,
)
from sage.runtime.engine import SageRuntime
from sage.runtime.health import check_health, get_sage_identity
from sage.runtime.metrics import get_metrics_collector
from sage.runtime.model_gateway import (
    ModelAdapter,
    ModelResponse,
    SAGERuntimeEnvelope,
    SAGEStateSnapshot,
)

# Preserve the established runtime-engine public API: sage.runtime.SAGERuntime
# is the operational engine consumed by sage.api and the existing service stack.
SAGERuntime = SageRuntime

# The model gateway remains a separate control-plane runtime. Expose it under
# its explicit gateway name so it cannot shadow the operational engine API.
SAGEModelRuntime = __import__("sage.runtime.model_gateway", fromlist=["SAGERuntime"]).SAGERuntime


def __getattr__(name: str) -> Any:
    """Lazy-load select modules to avoid circular imports at runtime initialization.

    This ensures sage.runtime:app maps directly to sage.api.app at runtime.
    """
    if name == "app":
        from sage.api import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "InitializationManager",
    "ModelAdapter",
    "ModelResponse",
    "SAGEModelRuntime",
    "SAGERuntime",
    "SAGERuntimeEnvelope",
    "SAGEStateSnapshot",
    "SageRuntime",
    "check_health",
    "discover_capabilities",
    "generate_capability_report",
    "generate_diagnostic_report",
    "generate_system_status_report",
    "get_metrics_collector",
    "get_sage_identity",
    "app",
]
