"""Read-only GitHub CLI PR telemetry adapter."""

import json
import subprocess
from typing import List, Tuple

from .base import BaseTelemetryAdapter
from ..models import FlightLifecycle, FlightManifest, ObservabilityState, OwnershipFingerprint


class GitHubTelemetryAdapter(BaseTelemetryAdapter):
    """Observe open PR metadata through ``gh`` without performing writes."""

    def fetch_active_manifests(self) -> Tuple[List[FlightManifest], ObservabilityState]:
        command = [
            "gh", "pr", "list", "--state", "open", "--json",
            "number,title,headRefName,baseRefName,mergeable,files,headRefOid,baseRefOid",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            payload = json.loads(result.stdout)
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
            self.observability_state = ObservabilityState.DEGRADED
            return [], self.observability_state

        manifests: List[FlightManifest] = []
        for pr in payload:
            files = {item["path"] for item in pr.get("files", []) if "path" in item}
            mergeable = pr.get("mergeable") == "MERGEABLE"
            manifests.append(
                FlightManifest(
                    flight_id=f"PR-{pr['number']}",
                    capability_target=pr.get("title", ""),
                    base_sha=pr.get("baseRefOid") or "UNKNOWN",
                    pr_number=pr["number"],
                    is_mergeable=mergeable,
                    lifecycle=FlightLifecycle.TESTING if mergeable else FlightLifecycle.RECONVERGING,
                    ownership=OwnershipFingerprint(files=files),
                )
            )
        self.observability_state = ObservabilityState.NOMINAL
        return manifests, self.observability_state
