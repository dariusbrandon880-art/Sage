"""SAGE Metrics Foundation - lightweight, thread-safe in-memory telemetry collector."""

import threading
from datetime import datetime, timezone
from typing import Any


class MetricsCollector:
    """Thread-safe in-memory collector for SAGE platform telemetry."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.RLock()  # Use Reentrant Lock to prevent deadlocks
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.events: list[dict[str, Any]] = []
        self.startup_time = datetime.now(timezone.utc)
        self.record_event("system_startup", {"timestamp": self.startup_time.isoformat()})

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a named counter metric.

        Args:
            name: Metric counter name.
            value: Integer value to increment by.
        """
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a named gauge metric.

        Args:
            name: Metric gauge name.
            value: Float value to set.
        """
        with self._lock:
            self.gauges[name] = float(value)

    def record_event(self, event_type: str, details: dict[str, Any] | None = None) -> None:
        """Record a structured diagnostic event.

        Args:
            event_type: Category/type of event.
            details: Additional context dictionary.
        """
        details_dict = details or {}
        with self._lock:
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "details": details_dict,
            }
            self.events.append(event)
            # Prevent infinite memory consumption by capping event history
            if len(self.events) > 1000:
                self.events.pop(0)

    def get_metrics(self) -> dict[str, Any]:
        """Compile and return current snapshot of collected metrics.

        Returns:
            Dictionary snapshot of counters, gauges, and recent events.
        """
        with self._lock:
            uptime = (datetime.now(timezone.utc) - self.startup_time).total_seconds()
            return {
                "uptime_seconds": uptime,
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "event_count": len(self.events),
                "recent_events": list(self.events[-10:]),
            }

    def clear(self) -> None:
        """Reset the collector state."""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.events.clear()
            self.startup_time = datetime.now(timezone.utc)
            self.record_event("metrics_cleared")


def get_metrics_collector() -> MetricsCollector:
    """Retrieve the global singleton instance of the MetricsCollector.

    Returns:
        MetricsCollector instance.
    """
    return MetricsCollector()
