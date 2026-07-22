"""Tests for SAGE Runtime Intelligence, Diagnostics, and Telemetry layers."""

import pytest
from unittest.mock import MagicMock
from sage.runtime import (
    SageRuntime,
    check_health,
    generate_diagnostic_report,
    generate_capability_report,
    get_metrics_collector,
    get_sage_identity,
    InitializationManager,
    generate_system_status_report,
    discover_capabilities,
)


class TestRuntimeIntelligence:
    """Test cases for runtime intelligence features."""

    def test_metrics_collector_singleton(self):
        """Verify that MetricsCollector functions as a thread-safe singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

        # Reset state for deterministic tests
        collector1.clear()
        metrics = collector1.get_metrics()
        assert metrics["counters"] == {}
        assert metrics["gauges"] == {}
        assert metrics["event_count"] == 1  # "metrics_cleared" event is recorded on clear

    def test_metrics_collection(self):
        """Verify metric recording, increment, gauges and events."""
        collector = get_metrics_collector()
        collector.clear()

        collector.increment("test_counter", 5)
        collector.increment("test_counter")
        collector.set_gauge("test_gauge", 4.2)
        collector.record_event("test_event", {"info": "context"})

        metrics = collector.get_metrics()
        assert metrics["counters"]["test_counter"] == 6
        assert metrics["gauges"]["test_gauge"] == 4.2
        assert metrics["event_count"] == 2  # metrics_cleared + test_event

        event_types = [ev["event_type"] for ev in metrics["recent_events"]]
        assert "test_event" in event_types

    def test_health_system_active_runtime(self):
        """Test health check output structure with a valid runtime."""
        runtime = SageRuntime()
        runtime.start()

        res = check_health(runtime)
        assert res["status"] in ["healthy", "degraded", "unhealthy"]
        assert res["runtime"] == "active"
        assert "components" in res
        assert "acr" in res["components"]
        assert "archive" in res["components"]
        assert "memory" in res["components"]
        assert "configuration" in res["components"]

        # Since subsystems are initialized by default, they should be "available"
        assert res["components"]["acr"] == "available"
        assert res["components"]["archive"] == "available"
        assert res["components"]["memory"] == "available"
        assert res["components"]["configuration"] == "available"
        assert res["status"] == "healthy"

    def test_health_system_inactive_runtime(self):
        """Test health check output structure with an inactive runtime."""
        runtime = SageRuntime()
        runtime.stop()

        res = check_health(runtime)
        assert res["runtime"] == "inactive"
        assert res["status"] == "healthy"  # components are still initialized/available

    def test_health_system_missing_runtime(self):
        """Test health check output structure with no runtime provided."""
        res = check_health(None)
        assert res["status"] == "unhealthy"
        assert res["runtime"] == "inactive"
        assert res["components"]["acr"] == "unavailable"

    def test_diagnostics_engine_report(self):
        """Test diagnostic report generation with a valid runtime."""
        runtime = SageRuntime()
        report = generate_diagnostic_report(runtime)

        assert "timestamp" in report
        assert "runtime_version" in report
        assert report["runtime_state"] in ["running", "stopped"]
        assert "available_modules" in report
        assert "missing_dependencies" in report
        assert "configuration_status" in report
        assert "component_readiness" in report
        assert "readiness_passed" in report

        # Verify configuration status was parsed
        assert report["configuration_status"]["loaded"] is True
        assert "storage_backends" in report["configuration_status"]

        # Verify component readiness of workspace & memory/archive
        assert "workspace" in report["component_readiness"]
        assert report["readiness_passed"] is True

    def test_capability_reporting(self):
        """Test capability reporting contains all 5 required capability groups."""
        runtime = SageRuntime()
        report = generate_capability_report(runtime)

        assert "timestamp" in report
        assert "total_capabilities" in report
        assert "active_capabilities" in report

        # Must include:
        # Runtime, ACR, Archive, Memory, Integration capabilities
        assert "runtime_capabilities" in report
        assert "acr_capabilities" in report
        assert "archive_capabilities" in report
        assert "memory_capabilities" in report
        assert "integration_capabilities" in report

        # Check a specific capability existence
        cap_names = [c["name"] for c in report["runtime_capabilities"]]
        assert "state_persistence" in cap_names
        assert "workspace_snapshots" in cap_names

        integration_names = [c["name"] for c in report["integration_capabilities"]]
        assert "chatgpt_connector" in integration_names
        assert "google_workspace_sync" in integration_names

    def test_runtime_operations_record_metrics(self):
        """Verify that starting SAGE and running operations update metrics."""
        collector = get_metrics_collector()
        collector.clear()

        runtime = SageRuntime()
        runtime.start()
        runtime.set_objective("Expand Intelligence")
        runtime.set_task("Create tests")
        runtime.checkpoint()

        metrics = collector.get_metrics()
        # Verify telemetry counters
        assert metrics["counters"]["runtime.initialization"] == 1
        assert metrics["counters"]["objectives.total"] == 1
        assert metrics["counters"]["tasks.total"] == 1
        assert metrics["counters"]["checkpoints.total"] == 1

        # Verify gauges
        assert metrics["gauges"]["runtime.active"] == 1.0

        # Verify events recorded
        event_types = [ev["event_type"] for ev in metrics["recent_events"]]
        assert "runtime_initialized" in event_types
        assert "runtime_started" in event_types
        assert "objective_set" in event_types
        assert "task_set" in event_types
        assert "checkpoint_created" in event_types

    def test_sage_identity_model(self):
        """Test SAGE Identity Model retrieves core properties correctly."""
        runtime = SageRuntime()
        runtime.start()

        identity = get_sage_identity(runtime)
        assert identity["system_name"] == "SAGE Autonomous Continuity Platform"
        assert identity["version"] == "1.1.0"
        assert "active_modules" in identity
        assert "sage.runtime" in identity["active_modules"]
        assert identity["initialization_state"] == "initialized"
        assert "capability_summary" in identity
        assert "health_state" in identity
        assert identity["health_state"] == "healthy"

    def test_controlled_initialization_flow(self):
        """Test the sequential controlled initialization sequence."""
        runtime = SageRuntime()
        init_mgr = InitializationManager(runtime)

        assert init_mgr.init_state == "uninitialized"
        summary = init_mgr.run_init_sequence()

        assert summary["status"] == "success"
        assert summary["initialization_state"] == "initialized"
        assert "load_configuration" in summary["steps_executed"]
        assert "discover_capabilities" in summary["steps_executed"]
        assert "verify_components" in summary["steps_executed"]
        assert init_mgr.init_state == "initialized"

    def test_initialization_failure_handling(self):
        """Test failure handling during initialization sequence when runtime is missing components."""
        # Test with a mock runtime with missing ACR
        mock_runtime = MagicMock()
        mock_runtime.is_running.return_value = False
        mock_runtime.acr = None  # Missing ACR

        init_mgr = InitializationManager(mock_runtime)
        summary = init_mgr.run_init_sequence()

        assert summary["status"] == "failed"
        assert summary["initialization_state"] == "failed"
        assert "required_components_unavailable" in summary["failures"]
        assert init_mgr.init_state == "failed"

    def test_system_status_report(self):
        """Test generation of the SAGE status report matches expected format."""
        runtime = SageRuntime()
        runtime.start()

        report = generate_system_status_report(runtime)
        assert "SAGE Status:" in report
        assert "- Runtime: active" in report
        assert "- Archive: available" in report
        assert "- Continuity: available" in report
        assert "- Capabilities: loaded" in report
        assert "- Validation: ready" in report

    def test_capability_flat_discovery(self):
        """Test discover_capabilities function returns list of active capability names."""
        runtime = SageRuntime()
        discovered = discover_capabilities(runtime)
        assert len(discovered) > 0
        assert "state_persistence" in discovered
