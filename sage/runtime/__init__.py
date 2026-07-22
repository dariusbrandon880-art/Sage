"""Runtime engine and intelligence layers for SAGE autonomous operations."""

from sage.runtime.engine import SageRuntime
from sage.runtime.health import check_health
from sage.runtime.diagnostics import generate_diagnostic_report
from sage.runtime.capability_report import generate_capability_report
from sage.runtime.metrics import get_metrics_collector

SAGERuntime = SageRuntime

__all__ = [
    "SageRuntime",
    "SAGERuntime",
    "check_health",
    "generate_diagnostic_report",
    "generate_capability_report",
    "get_metrics_collector",
]
