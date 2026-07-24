"""SAGE Runtime Integrity Layer (SRIL) Phase 1 Canonical Baseline Validation.

Provides tests confirming the sage.runtime:app invariant contract and TelemetrySink.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI


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
    """Verify sage.runtime exposes 'app'."""
    import sage.runtime

    assert hasattr(sage.runtime, "app")


def test_sril_runtime_contract_app_importable():
    """Verify 'app' can be imported from sage.runtime."""
    from sage.runtime import app

    assert app is not None


def test_sril_runtime_contract_callable():
    """Verify 'app' satisfies the callable runtime contract."""
    from sage.runtime import app

    assert isinstance(app, FastAPI)
    assert isinstance(app, Callable)


def test_sril_telemetry_sink_decoupled():
    """Verify structured telemetry support through TelemetrySink abstraction."""
    sink = TelemetrySink()
    sink.record_event("sril_contract_validation", {"status": "PASSED"})

    assert len(sink.records) == 1
    assert sink.records[0]["event_type"] == "sril_contract_validation"
    assert sink.records[0]["payload"]["status"] == "PASSED"
