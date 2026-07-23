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
]
