"""SAGE Reliability Foundation: incident monitoring, anomaly tracking, and safe recovery."""

import json
import uuid
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReliabilityIncident(BaseModel):
    """Data model representing a runtime error, anomaly, or exception incident."""

    id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: str  # low, medium, high, critical
    subsystem: str  # runtime, acr, archive, memory, validation
    error_message: str
    traceback_log: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReliabilityIncidentTracker:
    """Manages active logging, categorization, and diagnostics of SAGE runtime anomalies."""

    def __init__(self, storage_path: str = "sage_data/reliability"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.incidents: List[ReliabilityIncident] = []
        self._load_incidents()

    def _get_incidents_file_path(self) -> Path:
        return self.storage_path / "reliability_incidents.json"

    def _load_incidents(self) -> None:
        filepath = self._get_incidents_file_path()
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.incidents = [ReliabilityIncident(**inc) for inc in data]
            except Exception:
                self.incidents = []

    def save_incidents(self) -> None:
        filepath = self._get_incidents_file_path()
        with open(filepath, "w") as f:
            json.dump([inc.model_dump() for inc in self.incidents], f, indent=2, default=str)

    def log_incident(
        self,
        severity: str,
        subsystem: str,
        error_message: str,
        exc: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReliabilityIncident:
        """Capture and categorize a production exception or system anomaly securely."""
        tb_log = None
        if exc is not None:
            tb_log = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        incident = ReliabilityIncident(
            severity=severity,
            subsystem=subsystem,
            error_message=error_message,
            traceback_log=tb_log,
            metadata=metadata or {},
        )
        self.incidents.append(incident)
        self.save_incidents()

        # Update telemetry metrics via MetricsCollector
        from sage.runtime.metrics import get_metrics_collector

        get_metrics_collector().increment(f"reliability.incidents.{severity}")
        get_metrics_collector().record_event(
            "reliability_incident_logged", {"incident_id": incident.id, "severity": severity}
        )

        return incident

    def get_active_incidents(self, min_severity: Optional[str] = None) -> List[ReliabilityIncident]:
        """List current incidents filtered by minimum severity level."""
        severity_ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if not min_severity:
            return self.incidents

        min_rank = severity_ranks.get(min_severity.lower(), 1)
        return [
            inc for inc in self.incidents if severity_ranks.get(inc.severity.lower(), 1) >= min_rank
        ]
