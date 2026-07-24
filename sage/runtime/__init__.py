"""Runtime engine and intelligence layers for SAGE autonomous operations."""

from sage.runtime.engine import SageRuntime
from sage.runtime.health import check_health, get_sage_identity
from sage.runtime.diagnostics import (
    generate_diagnostic_report,
    InitializationManager,
    generate_system_status_report,
)
from sage.runtime.capability_report import generate_capability_report, discover_capabilities
from sage.runtime.metrics import get_metrics_collector

SAGERuntime = SageRuntime

__all__ = [
    "SageRuntime",
    "SAGERuntime",
    "check_health",
    "get_sage_identity",
    "generate_diagnostic_report",
    "InitializationManager",
    "generate_system_status_report",
    "generate_capability_report",
    "discover_capabilities",
    "get_metrics_collector",
    "app",
]


def __getattr__(name: str):
    """Lazy-load app to prevent circular imports during runtime startup."""
    if name == "app":
        try:
            from sage.api import app as fastapi_app

            return fastapi_app
        except Exception as e:
            import sys
            import logging

            logger = logging.getLogger("sage.runtime")
            logger.error(
                f"FATAL: SAGE Runtime failed to load invariant entry boundary: {str(e)}",
                exc_info=True,
            )
            sys.exit(1)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
