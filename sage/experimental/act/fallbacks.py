"""SAGE Experimental Resilient Integration Fallbacks.

Implements Milestone 1.2: Resilient Integration Fallbacks under experimental isolation.
Provides non-crashing try-except wrappers and mock diagnostics for Google Workspace credentials lookup.
"""

import os
import json
import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger("sage.experimental.act.fallbacks")


class ResilientIntegrationBridge:
    """Provides graceful degradation and mock-resilient fallback behaviors for third-party integrations."""

    def __init__(self, fallback_enabled: bool = True):
        """Initialize the resilient integration bridge."""
        self.fallback_enabled = fallback_enabled

    def validate_credentials(self, credentials_path: str) -> Dict[str, Any]:
        """Checks for Google Workspace credentials and returns sync capability diagnostics.

        Instead of throwing exceptions on missing files, returns a degraded status.

        Args:
            credentials_path: Path to the OAuth credentials file.

        Returns:
            A dictionary containing status, reason, sync_enabled, and mock_mode indicators.
        """
        if not credentials_path or not isinstance(credentials_path, str):
            return {
                "status": "DEGRADED",
                "reason": "Invalid credentials path format.",
                "sync_enabled": False,
                "mock_mode": True,
            }

        if not os.path.exists(credentials_path):
            return {
                "status": "DEGRADED",
                "reason": f"Google Workspace credentials file not found at: '{credentials_path}'.",
                "sync_enabled": False,
                "mock_mode": True,
            }

        try:
            with open(credentials_path, "r", encoding="utf-8") as f:
                json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return {
                "status": "DEGRADED",
                "reason": f"Corrupted or unreadable credentials file: {e}",
                "sync_enabled": False,
                "mock_mode": True,
            }

        return {
            "status": "HEALTHY",
            "reason": "Valid Google credentials loaded successfully.",
            "sync_enabled": True,
            "mock_mode": False,
        }

    def execute_sync_safely(
        self,
        credentials_path: str,
        sync_action: Callable[[], Any],
        fallback_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Executes a synchronization routine safely, falling back gracefully on failure.

        Args:
            credentials_path: Path to OAuth credentials.
            sync_action: A callable function executing live API sync.
            fallback_payload: Standardized mock data payload to fall back to if credentials are missing.

        Returns:
            A dictionary containing execution results and diagnostic tracking.
        """
        diagnostics = self.validate_credentials(credentials_path)

        if not diagnostics["sync_enabled"]:
            if self.fallback_enabled:
                logger.warning("Resilient Fallback: Sync action degraded. Utilizing mock fallback payload.")
                return {
                    "status": "FALLBACK_ACTIVE",
                    "result": fallback_payload,
                    "diagnostics": diagnostics,
                }
            else:
                raise FileNotFoundError(diagnostics["reason"])

        try:
            result = sync_action()
            return {
                "status": "SUCCESS",
                "result": result,
                "diagnostics": diagnostics,
            }
        except Exception as e:
            if self.fallback_enabled:
                logger.error(f"Resilient Fallback: Live sync raised error: {e}. Executing graceful fallback.")
                return {
                    "status": "FALLBACK_ACTIVE",
                    "result": fallback_payload,
                    "diagnostics": {
                        "status": "DEGRADED",
                        "reason": f"Live action execution failed: {e}",
                        "sync_enabled": False,
                        "mock_mode": True,
                    },
                }
            else:
                raise e
