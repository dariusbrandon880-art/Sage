"""Telemetry adapter contracts and observability states."""

from abc import ABC, abstractmethod
from typing import List, Tuple

from ..models import FlightManifest, ObservabilityState


class TelemetryException(Exception):
    """Raised when telemetry cannot provide a trustworthy view."""


class BaseTelemetryAdapter(ABC):
    """Abstract source adapter with explicit observability reporting."""

    def __init__(self) -> None:
        self.observability_state = ObservabilityState.NOMINAL

    @abstractmethod
    def fetch_active_manifests(self) -> Tuple[List[FlightManifest], ObservabilityState]:
        """Return observed manifests and the adapter's current trust state."""

    def validate_dispatch_safety(self) -> bool:
        """Allow new dispatch only when telemetry is not offline."""
        return self.observability_state != ObservabilityState.OFFLINE
