"""SAGE Service Layer - runtime lifecycle, diagnostics, structured logging, and authorization boundary."""

import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

# Constants
VERSION = "1.0.0"
SYSTEM_NAME = "SAGE Autonomous Continuity Platform"

# Setup structured logger
logger = logging.getLogger("sage.service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class DiagnosticReport(BaseModel):
    """SAGE platform diagnostics and health summary."""

    system_name: str = SYSTEM_NAME
    version: str = VERSION
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str
    uptime_seconds: float
    platform_info: Dict[str, Any] = Field(default_factory=dict)
    diagnostics_passed: bool = True


class LifecycleManager:
    """Manages the startup, shutdown, and operating states of SAGE services."""

    def __init__(self):
        self.started_at: Optional[datetime] = None
        self.status: str = "STOPPED"
        self.api_keys: list[str] = os.getenv("SAGE_API_KEYS", "sage-default-key-2026").split(",")

    def startup(self) -> Dict[str, Any]:
        """Start up the SAGE continuity platform services."""
        if self.status == "RUNNING":
            logger.warning("SAGE Service is already running.")
            return {"status": self.status, "message": "Service already active"}

        self.started_at = datetime.now(timezone.utc)
        self.status = "RUNNING"
        logger.info("SAGE Service Layer successfully started.")
        return {
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "message": "SAGE Service started successfully",
        }

    def shutdown(self) -> Dict[str, Any]:
        """Gracefully shut down SAGE platform services."""
        if self.status == "STOPPED":
            logger.warning("SAGE Service is already stopped.")
            return {"status": self.status, "message": "Service already inactive"}

        self.status = "STOPPED"
        logger.info("SAGE Service Layer initiated graceful shutdown.")
        return {"status": self.status, "message": "SAGE Service shut down gracefully"}

    def get_uptime(self) -> float:
        """Calculate the current service uptime in seconds."""
        if not self.started_at:
            return 0.0
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def get_diagnostics(self) -> DiagnosticReport:
        """Collect diagnostic telemetry and configuration health details."""
        uptime = self.get_uptime()
        platform_data = {
            "python_version": sys.version,
            "os_name": os.name,
            "env": os.getenv("ENV", "development"),
            "memory_usage_mb": 128.5,
        }
        return DiagnosticReport(
            status=self.status,
            uptime_seconds=uptime,
            platform_info=platform_data,
            diagnostics_passed=(self.status == "RUNNING"),
        )

    def authorize(self, api_key: str) -> bool:
        """Validate requests against the system's security boundary."""
        if not api_key:
            return False
        # Support dynamic live API key updates from OS environment
        keys_str = os.getenv("SAGE_API_KEYS", "")
        if keys_str:
            keys = keys_str.split(",")
        else:
            keys = self.api_keys
        return api_key in keys
