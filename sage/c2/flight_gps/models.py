"""Core state models for the SAGE C2 Flight GPS."""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Optional, Set


class AirspaceStatus(Enum):
    """Safety classification of a capability target space."""

    CLEAR = "CLEAR"
    SHARED = "SHARED"
    DEPENDENT = "DEPENDENT"
    OCCUPIED = "OCCUPIED"
    STALE = "STALE"


class FlightLifecycle(Enum):
    """Execution progress of a flight, independent from airspace safety."""

    PROPOSED = "PROPOSED"
    RESERVED = "RESERVED"
    ACTIVE = "ACTIVE"
    TESTING = "TESTING"
    RECONVERGING = "RECONVERGING"
    INTEGRATED = "INTEGRATED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class ObservabilityState(Enum):
    """Trust level of the control tower's telemetry view."""

    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


@dataclass
class OwnershipFingerprint:
    """Code and artifact boundaries claimed by a flight."""

    files: Set[str] = field(default_factory=set)
    modules: Set[str] = field(default_factory=set)
    symbols: Set[str] = field(default_factory=set)
    artifacts: Set[str] = field(default_factory=set)


@dataclass
class FlightManifest:
    """Observable state for a candidate or airborne flight."""

    flight_id: str
    capability_target: str
    base_sha: str
    ownership: OwnershipFingerprint = field(default_factory=OwnershipFingerprint)
    lifecycle: FlightLifecycle = FlightLifecycle.PROPOSED
    airspace: AirspaceStatus = AirspaceStatus.CLEAR
    session_id: str = "UNKNOWN"
    pr_number: Optional[int] = None
    is_mergeable: bool = True
    heartbeat_ttl_seconds: float = 120.0
    last_ping_utc: float = field(default_factory=time.time)

    def is_heartbeat_expired(self, now: Optional[float] = None) -> bool:
        """Return whether the flight has exceeded its heartbeat TTL."""
        current = time.time() if now is None else now
        return current - self.last_ping_utc > self.heartbeat_ttl_seconds

    def refresh_heartbeat(self, now: Optional[float] = None) -> None:
        """Refresh the flight ownership heartbeat."""
        self.last_ping_utc = time.time() if now is None else now
