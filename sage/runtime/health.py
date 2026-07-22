"""SAGE Runtime Health System - dynamic health monitoring for core sub-systems."""

import os
from typing import Dict, Any, Optional
from sage.runtime.metrics import get_metrics_collector


def check_health(runtime: Optional[Any] = None) -> Dict[str, Any]:
    """Dynamically determine whether core SAGE systems are available.

    Args:
        runtime: Active SAGE runtime instance to inspect.

    Returns:
        Structured health status dictionary.
    """
    # Track the health check invocation
    metrics = get_metrics_collector()
    metrics.increment("health_checks.total")

    # Default components status
    components = {
        "acr": "unavailable",
        "archive": "unavailable",
        "memory": "unavailable",
        "configuration": "unavailable"
    }

    runtime_active = "inactive"
    if runtime is not None:
        # Check Runtime Initialization & active state
        if hasattr(runtime, "is_running") and runtime.is_running():
            runtime_active = "active"
        else:
            runtime_active = "inactive"

        # Check ACR Availability
        if hasattr(runtime, "acr") and runtime.acr is not None:
            try:
                # Attempt a simple, safe operation to verify responsiveness
                runtime.acr.get_session_depth()
                components["acr"] = "available"
            except Exception as e:
                components["acr"] = f"error: {str(e)}"
                metrics.record_event("health_check.acr_error", {"error": str(e)})

        # Check Archive Availability
        if hasattr(runtime, "archive") and runtime.archive is not None:
            try:
                # Attempt to retrieve/list entries or verify directory is accessible
                runtime.archive.list_all()
                components["archive"] = "available"
            except Exception as e:
                components["archive"] = f"error: {str(e)}"
                metrics.record_event("health_check.archive_error", {"error": str(e)})

        # Check Memory Availability
        if hasattr(runtime, "memory") and runtime.memory is not None:
            try:
                # Attempt a safe read operation to verify responsiveness
                runtime.memory.list_all()
                components["memory"] = "available"
            except Exception as e:
                components["memory"] = f"error: {str(e)}"
                metrics.record_event("health_check.memory_error", {"error": str(e)})

        # Check Configuration Availability
        if hasattr(runtime, "config") and runtime.config is not None:
            components["configuration"] = "available"
    else:
        metrics.record_event("health_check.missing_runtime")

    # Assess overall status. All requested components must be "available"
    # (acr, archive, memory, configuration)
    essential_components = ["acr", "archive", "memory", "configuration"]
    available_count = sum(1 for c in essential_components if components.get(c) == "available")

    if available_count == len(essential_components):
        status = "healthy"
    elif available_count > 0:
        status = "degraded"
    else:
        status = "unhealthy"

    # Record health status metric
    metrics.set_gauge("health.status_score", float(available_count) / len(essential_components))

    return {
        "status": status,
        "runtime": runtime_active,
        "components": components
    }
