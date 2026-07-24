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
]
