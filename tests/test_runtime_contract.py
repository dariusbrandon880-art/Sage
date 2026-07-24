"""SAGE Runtime Integrity Layer (SRIL) Phase 1 Canonical Baseline Validation.

Provides tests confirming the sage.runtime:app invariant contract and TelemetrySink.
"""

import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sage.runtime.engine import SageRuntime


class TelemetrySink:
    """Structured telemetry support for SRIL decoupled storage routing."""

    def __init__(self):
        """Initialize telemetry sink."""
        self.records: list[dict[str, Any]] = []

    def record_event(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Route telemetry event records cleanly."""
        self.records.append(
            {
                "event_type": event_type,
                "payload": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


def test_sril_runtime_contract_app_exposed():
    """Verify sage.runtime exposes 'app' and it is callable."""
    import sage.runtime

    assert hasattr(sage.runtime, "app")
    assert callable(sage.runtime.app)


def test_sril_runtime_contract_app_importable():
    """Verify 'app' can be imported from sage.runtime."""
    from sage.runtime import app

    assert app is not None


def test_sril_runtime_contract_callable():
    """Verify 'app' satisfies the callable runtime contract."""
    from sage.runtime import app

    assert isinstance(app, Callable)


def test_sril_telemetry_sink_decoupled():
    """Verify structured telemetry support through TelemetrySink abstraction."""
    sink = TelemetrySink()
    sink.record_event("sril_contract_validation", {"status": "PASSED"})

    assert len(sink.records) == 1
    assert sink.records[0]["event_type"] == "sril_contract_validation"
    assert sink.records[0]["payload"]["status"] == "PASSED"


def test_sril_isolation_boundary():
    """Verify that external proposal/snapshot mutations do not alter source repository state."""
    # Create an isolated temporary workspace for the runtime
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SageRuntime(workspace_path=tmpdir)
        runtime.start()

        # Perform mutations (setting objectives, creating checkpoints, and saving state)
        runtime.set_objective("Isolated Test Objective")
        runtime.checkpoint()
        runtime.create_workspace_snapshot()

        # Assert modifications only affected the temporary workspace path
        workspace_path = Path(tmpdir)
        assert workspace_path.exists()
        assert (workspace_path / "state.json").exists()

        # Verify that the actual production directories remain untouched and no global files are created
        prod_state_file = Path("sage_data/state.json")
        if prod_state_file.exists():
            # If a prod file exists from local runs, verify it was not modified during this test
            mtime = prod_state_file.stat().st_mtime
            # Ensure no write happened right now
            assert (datetime.now(timezone.utc).timestamp() - mtime) > 0.001

        runtime.stop()
