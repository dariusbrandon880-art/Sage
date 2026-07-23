"""SAGE Diagnostics Engine & Initialization Manager - controlled startup and status reporting."""

import importlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from sage.runtime.metrics import get_metrics_collector


class InitializationManager:
    """Manages the controlled, sequential startup sequence of SAGE."""

    def __init__(self, runtime: Optional[Any] = None):
        """Initialize the InitializationManager.

        Args:
            runtime: SAGE runtime instance to initialize.
        """
        self.runtime = runtime
        self.init_state = "uninitialized"

    def run_init_sequence(self) -> Dict[str, Any]:
        """Perform SAGE's controlled startup sequence: load config, discover capabilities, verify required components.

        Returns:
            Structured initialization summary.
        """
        self.init_state = "initializing"
        metrics = get_metrics_collector()
        metrics.record_event("init_sequence.started")

        steps_executed = []
        failures = []

        # 1. Load configuration
        try:
            from sage.config.settings import SageConfig

            SageConfig.from_env()
            steps_executed.append("load_configuration")
            metrics.increment("init.step.load_configuration")
        except Exception as e:
            failures.append(f"load_configuration_failed: {str(e)}")

        # 2. Discover available capabilities
        try:
            from sage.runtime.capability_report import generate_capability_report

            generate_capability_report(self.runtime)
            steps_executed.append("discover_capabilities")
            metrics.increment("init.step.discover_capabilities")
        except Exception as e:
            failures.append(f"discover_capabilities_failed: {str(e)}")

        # 3. Verify required components (ACR, Memory, Archive)
        try:
            from sage.runtime.health import check_health

            h = check_health(self.runtime)
            if h.get("status") in ["unhealthy", "degraded"]:
                failures.append("required_components_unavailable")
            steps_executed.append("verify_components")
            metrics.increment("init.step.verify_components")
        except Exception as e:
            failures.append(f"verify_components_failed: {str(e)}")

        # 4. Update SAGE instance state
        if failures:
            self.init_state = "failed"
            metrics.record_event("init_sequence.failed", {"failures": failures})
            if self.runtime is not None:
                self.runtime._init_failed = True
        else:
            self.init_state = "initialized"
            metrics.record_event("init_sequence.success")
            if self.runtime is not None:
                self.runtime._init_failed = False

        return {
            "status": "success" if not failures else "failed",
            "initialization_state": self.init_state,
            "steps_executed": steps_executed,
            "failures": failures,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def generate_system_status_report(runtime: Optional[Any] = None) -> str:
    """Generate a unified SAGE runtime status report matching the required text layout.

    Args:
        runtime: Active SAGE runtime instance to inspect.

    Returns:
        Formatted SAGE Status text report string.
    """
    from sage.runtime.health import check_health
    from sage.runtime.capability_report import generate_capability_report

    health_info = check_health(runtime)
    components = health_info.get("components", {})

    runtime_state = "active" if health_info.get("runtime") == "active" else "inactive"
    archive_state = "available" if components.get("archive") == "available" else "unavailable"
    continuity_state = "available" if components.get("acr") == "available" else "unavailable"

    capabilities_state = "loaded"
    try:
        generate_capability_report(runtime)
    except Exception:
        capabilities_state = "failed"

    validation_state = "ready"
    if (
        runtime is None
        or getattr(runtime, "validation", None) is None
        or components.get("memory") != "available"
    ):
        validation_state = "uninitialized"

    report_lines = [
        "SAGE Status:",
        f"- Runtime: {runtime_state}",
        f"- Archive: {archive_state}",
        f"- Continuity: {continuity_state}",
        f"- Capabilities: {capabilities_state}",
        f"- Validation: {validation_state}",
    ]

    return "\n".join(report_lines)


def generate_diagnostic_report(runtime: Optional[Any] = None) -> Dict[str, Any]:
    """Produce a comprehensive, dynamic SAGE runtime diagnostic report.

    Args:
        runtime: Active SAGE runtime instance to diagnose.

    Returns:
        Structured diagnostic report.
    """
    metrics = get_metrics_collector()
    metrics.increment("diagnostics.total")
    metrics.record_event("diagnostics.triggered")

    # 1. Runtime Version & State
    # Retrieve system version from sage.service or use a default fallback
    version = "1.1.0"
    try:
        from sage.service import VERSION

        version = VERSION
    except Exception:
        pass

    state_info = {
        "active": False,
        "current_objective": None,
        "active_task": None,
        "blockers": [],
        "session_depth": 0,
        "memory_count": 0,
        "archive_count": 0,
        "decision_count": 0,
    }

    if runtime is not None:
        state_info["active"] = runtime.is_running()
        if hasattr(runtime, "current_state"):
            state_info["current_objective"] = runtime.current_state.current_objective
            state_info["active_task"] = runtime.current_state.active_task
            state_info["blockers"] = list(runtime.current_state.blockers)
        if hasattr(runtime, "acr"):
            state_info["session_depth"] = runtime.acr.get_session_depth()
        if hasattr(runtime, "memory"):
            state_info["memory_count"] = len(runtime.memory.list_all())
        if hasattr(runtime, "archive"):
            state_info["archive_count"] = len(runtime.archive.list_all())
        if hasattr(runtime, "decisions"):
            state_info["decision_count"] = len(runtime.decisions.list_all())

    # 2. Available Modules & Missing Dependencies
    # List of dependencies/modules to audit
    audit_modules = {
        "fastapi": "FastAPI Web Framework",
        "pydantic": "Pydantic Data Validation",
        "pydantic_settings": "Pydantic Settings",
        "uvicorn": "Uvicorn ASGI Server",
        "httpx": "HTTPX HTTP Client",
        "pytest": "Pytest Testing Framework",
        "black": "Black Code Formatter",
        "ruff": "Ruff Linter",
        "mypy": "Mypy Type Checker",
        "sage.acr": "SAGE ACR Subsystem",
        "sage.archive": "SAGE Archive Subsystem",
        "sage.memory": "SAGE Memory Subsystem",
        "sage.validation": "SAGE Validation Subsystem",
        "sage.service": "SAGE Service Layer",
        "sage.integration": "SAGE Integration Layer",
        "sage.decision": "SAGE Decision Subsystem",
    }

    available_modules = []
    missing_dependencies = []

    for mod_name, desc in audit_modules.items():
        try:
            importlib.import_module(mod_name)
            available_modules.append(f"{mod_name} ({desc})")
        except ImportError:
            missing_dependencies.append(mod_name)

    # 3. Configuration Status
    config_status = {
        "loaded": False,
        "debug_mode": False,
        "environment": "unknown",
        "storage_backends": {},
        "security_configured": False,
    }

    # Try to load current SageConfig settings if available
    try:
        from sage.config.settings import SageConfig

        config = SageConfig.from_env()
        config_status["loaded"] = True
        config_status["debug_mode"] = config.debug
        config_status["environment"] = config.env
        config_status["storage_backends"] = {
            "memory": config.memory_backend,
            "archive": config.archive_backend,
        }
        config_status["security_configured"] = bool(
            config.sage_api_keys and config.sage_api_keys != "sage-default-key-2026"
        )
    except Exception as e:
        config_status["error"] = f"Failed to inspect configuration: {str(e)}"

    # 4. Component Readiness (Dynamic Subsystem Checks)
    component_readiness = {
        "workspace": "unconfigured",
        "memory_store": "uninitialized",
        "archive_store": "uninitialized",
        "decision_tracker": "uninitialized",
    }

    if runtime is not None:
        # Check workspace writeability
        ws_path = Path(runtime.workspace_path)
        try:
            ws_path.mkdir(parents=True, exist_ok=True)
            test_file = ws_path / ".diagnostics_write_test"
            with open(test_file, "w") as f:
                f.write("ready")
            test_file.unlink()
            component_readiness["workspace"] = "ready_writable"
        except Exception as e:
            component_readiness["workspace"] = f"write_failed: {str(e)}"

        # Memory Store Check
        if hasattr(runtime, "memory") and runtime.memory is not None:
            try:
                mem_path = Path(runtime.memory_path)
                component_readiness["memory_store"] = {
                    "status": "ready",
                    "path": str(mem_path),
                    "exists": mem_path.exists(),
                    "cached_count": len(runtime.memory.list_all()),
                }
            except Exception as e:
                component_readiness["memory_store"] = f"error: {str(e)}"

        # Archive Store Check
        if hasattr(runtime, "archive") and runtime.archive is not None:
            try:
                arch_path = Path(runtime.archive_path)
                component_readiness["archive_store"] = {
                    "status": "ready",
                    "path": str(arch_path),
                    "exists": arch_path.exists(),
                    "cached_count": len(runtime.archive.list_all()),
                }
            except Exception as e:
                component_readiness["archive_store"] = f"error: {str(e)}"

        # Decision Tracker Check
        if hasattr(runtime, "decisions") and runtime.decisions is not None:
            try:
                dec_path = Path(runtime.decisions_path)
                component_readiness["decision_tracker"] = {
                    "status": "ready",
                    "path": str(dec_path),
                    "exists": dec_path.exists(),
                    "cached_count": len(runtime.decisions.list_all()),
                }
            except Exception as e:
                component_readiness["decision_tracker"] = f"error: {str(e)}"

    # Check overall readiness score
    is_ready = (
        component_readiness.get("workspace") == "ready_writable"
        and isinstance(component_readiness.get("memory_store"), dict)
        and component_readiness["memory_store"].get("status") == "ready"
        and isinstance(component_readiness.get("archive_store"), dict)
        and component_readiness["archive_store"].get("status") == "ready"
        and isinstance(component_readiness.get("decision_tracker"), dict)
        and component_readiness["decision_tracker"].get("status") == "ready"
    )

    metrics.set_gauge("diagnostics.readiness_passed", 1.0 if is_ready else 0.0)

    # Compile report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime_version": version,
        "runtime_state": "running" if state_info["active"] else "stopped",
        "state_details": state_info,
        "available_modules": available_modules,
        "missing_dependencies": missing_dependencies,
        "configuration_status": config_status,
        "component_readiness": component_readiness,
        "readiness_passed": is_ready,
    }

    # Add SAGE text status report for quick reference
    try:
        report["status_text_report"] = generate_system_status_report(runtime)
    except Exception:
        pass

    return report
