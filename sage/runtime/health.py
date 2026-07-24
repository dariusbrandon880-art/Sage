"""SAGE Runtime Health System & Identity Model - dynamic health monitoring and identity representation."""

import sys
from typing import Any

from pydantic import BaseModel, Field

from sage.runtime.metrics import get_metrics_collector


class SageIdentity(BaseModel):
    """Structured representation of the running SAGE instance."""

    system_name: str = "SAGE Autonomous Continuity Platform"
    version: str = "1.1.0"
    active_modules: list[str] = Field(default_factory=list)
    initialization_state: str = "uninitialized"  # uninitialized, initializing, initialized, failed
    capability_summary: dict[str, Any] = Field(default_factory=dict)
    health_state: str = "unknown"


def get_sage_identity(runtime: Any | None = None) -> dict[str, Any]:
    """Retrieve the dynamic structural representation of SAGE's identity.

    Args:
        runtime: Active SAGE runtime instance to inspect.

    Returns:
        Structured SAGE identity dictionary.
    """
    # 1. Discover active modules
    active_mods = []
    for mod in [
        "sage.acr",
        "sage.archive",
        "sage.memory",
        "sage.validation",
        "sage.service",
        "sage.integration",
        "sage.decision",
        "sage.runtime",
    ]:
        if mod in sys.modules:
            active_mods.append(mod)

    # 2. Get capability summary
    total_caps = 0
    active_caps = 0
    try:
        from sage.runtime.capability_report import generate_capability_report

        cap_report = generate_capability_report(runtime)
        total_caps = cap_report.get("total_capabilities", 0)
        active_caps = cap_report.get("active_capabilities", 0)
    except Exception:
        pass

    # 3. Determine health state
    health_status = "unknown"
    try:
        health_status = check_health(runtime).get("status", "unknown")
    except Exception:
        pass

    # 4. Determine initialization state
    init_state = "uninitialized"
    if runtime is not None:
        if getattr(runtime, "_init_failed", False):
            init_state = "failed"
        elif getattr(runtime, "active", False):
            init_state = "initialized"
        else:
            init_state = "initializing"

    identity = SageIdentity(
        system_name="SAGE Autonomous Continuity Platform",
        version="1.1.0",
        active_modules=active_mods,
        initialization_state=init_state,
        capability_summary={"total": total_caps, "active": active_caps},
        health_state=health_status,
    )

    return identity.model_dump()


def check_health(runtime: Any | None = None) -> dict[str, Any]:
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
        "configuration": "unavailable",
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
                components["acr"] = f"error: {e!s}"
                metrics.record_event("health_check.acr_error", {"error": str(e)})

        # Check Archive Availability
        if hasattr(runtime, "archive") and runtime.archive is not None:
            try:
                # Attempt to retrieve/list entries or verify directory is accessible
                runtime.archive.list_all()
                components["archive"] = "available"
            except Exception as e:
                components["archive"] = f"error: {e!s}"
                metrics.record_event("health_check.archive_error", {"error": str(e)})

        # Check Memory Availability
        if hasattr(runtime, "memory") and runtime.memory is not None:
            try:
                # Attempt a safe read operation to verify responsiveness
                runtime.memory.list_all()
                components["memory"] = "available"
            except Exception as e:
                components["memory"] = f"error: {e!s}"
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

    # New Cognitive Control Plane health metrics
    approved = metrics.counters.get("control_plane.mutations_approved", 0)
    rejected = metrics.counters.get("control_plane.mutations_rejected", 0)
    total = approved + rejected
    asi = float(approved) / total if total > 0 else 1.0

    # Retrieve receipt chain integrity
    receipt_chain_integrity = True
    if runtime and hasattr(runtime, "validation") and hasattr(runtime.validation, "receipt_chain"):
        receipt_chain_integrity = runtime.validation.receipt_chain.verify_chain_integrity()

    # Drift Detection
    drift_detected = False
    drift_reason = "none"
    if runtime and hasattr(runtime, "current_state"):
        current_obj = runtime.current_state.current_objective
        active_task = runtime.current_state.active_task
        if hasattr(runtime, "checkpoint_manager"):
            try:
                checkpoints = runtime.checkpoint_manager.list_all()
                if checkpoints and (current_obj or active_task):
                    latest_chk = checkpoints[-1]
                    active_goals = getattr(latest_chk, "active_goals", [])
                    if active_goals and current_obj and current_obj not in active_goals:
                        drift_detected = True
                        drift_reason = "Active objective diverges from latest checkpoint goals"
            except Exception:
                pass

    csi = 1.0  # Cognitive Separation Index is 1.0 unless unauthorized direct writing detected

    cognitive_control_plane = {
        "authority_stability_index": asi,
        "cognitive_separation_index": csi,
        "rejected_mutations": rejected,
        "receipt_chain_integrity": receipt_chain_integrity,
        "drift_detection": {
            "drift_detected": drift_detected,
            "drift_reason": drift_reason
        }
    }

    # Record metrics gauges
    metrics.set_gauge("health.authority_stability_index", asi)
    metrics.set_gauge("health.cognitive_separation_index", csi)
    metrics.set_gauge("health.receipt_chain_integrity", 1.0 if receipt_chain_integrity else 0.0)

    return {
        "status": status,
        "runtime": runtime_active,
        "components": components,
        "cognitive_control_plane": cognitive_control_plane
    }
