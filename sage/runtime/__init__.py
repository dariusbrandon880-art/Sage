"""Runtime engine and intelligence layers for SAGE autonomous operations."""

from sage.runtime.capability_report import discover_capabilities, generate_capability_report
from sage.runtime.diagnostics import (
    InitializationManager,
    generate_diagnostic_report,
    generate_system_status_report,
)
from sage.runtime.engine import SageRuntime
from sage.runtime.health import check_health, get_sage_identity
from sage.runtime.metrics import get_metrics_collector

SAGERuntime = SageRuntime

__all__ = [
    "InitializationManager",
    "SAGERuntime",
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

def __getattr__(name: str):
    """Lazy-load the FastAPI app to prevent circular dependencies on initialization."""
    if name == "app":
        import sys
        from sage.api import app as fastapi_app
        # Cache it directly inside the module to optimize subsequent lookups
        setattr(sys.modules[__name__], "app", fastapi_app)
        return list_all_exports_if_needed(fastapi_app)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def list_all_exports_if_needed(fastapi_app):
    return fastapi_app
