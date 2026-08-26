"""Local Git telemetry adapter."""

import subprocess
from typing import List, Tuple

from .base import BaseTelemetryAdapter
from ..models import FlightManifest, ObservabilityState, OwnershipFingerprint


class GitTelemetryAdapter(BaseTelemetryAdapter):
    """Observe local branches without mutating repository state."""

    def fetch_active_manifests(self) -> Tuple[List[FlightManifest], ObservabilityState]:
        try:
            result = subprocess.run(
                ["git", "for-each-ref", "refs/remotes", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            self.observability_state = ObservabilityState.OFFLINE
            return [], self.observability_state
        manifests = []
        for ref in filter(None, result.stdout.splitlines()):
            manifests.append(
                FlightManifest(
                    flight_id=f"REF-{ref}",
                    capability_target=ref,
                    base_sha="UNKNOWN",
                    ownership=OwnershipFingerprint(),
                )
            )
        self.observability_state = ObservabilityState.NOMINAL
        return manifests, self.observability_state
