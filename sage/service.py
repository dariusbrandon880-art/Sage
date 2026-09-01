"""SAGE Service Layer - runtime lifecycle, diagnostics, structured logging, and authorization boundary."""

import hashlib
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional

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
    platform_info: dict[str, Any] = Field(default_factory=dict)
    diagnostics_passed: bool = True


class LifecycleManager:
    """Manages the startup, shutdown, and operating states of SAGE services.
    
    This is the authorization boundary for external agents (ChatGPT, etc).
    It reads API keys from environment (SAGE_API_KEYS) and validates all requests.
    """

    def __init__(self):
        self.started_at: Optional[datetime] = None
        self.status: str = "STOPPED"
        self.api_key_hashes: set[str] = set()
        self.session_tokens: dict[str, dict[str, Any]] = {}
        self.load_api_keys_from_environment()

    def load_api_keys_from_environment(self) -> None:
        """Load and hash API keys from Render environment.
        
        Reads SAGE_API_KEYS env var (Render will auto-generate this).
        Keys are stored as SHA256 hashes to avoid exposing them in memory dumps.
        """
        keys_str = os.getenv("SAGE_API_KEYS", "")
        
        if not keys_str:
            # Fallback for local development only
            if os.getenv("ENV", "production") != "production":
                logger.warning("SAGE_API_KEYS not set. Using dev fallback key.")
                keys_str = "sage-dev-key-2026"
            else:
                logger.warning("SAGE_API_KEYS not set in production. Auth will FAIL CLOSED.")
                return
        
        # Parse comma or colon-delimited keys
        keys = [
            k.strip() 
            for k in (keys_str.replace(":", ",").split(",")) 
            if k.strip()
        ]
        
        for key in keys:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            self.api_key_hashes.add(key_hash)
        
        logger.info(f"Loaded {len(self.api_key_hashes)} API key(s) from environment")

    def startup(self) -> dict[str, Any]:
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
            "auth_ready": len(self.api_key_hashes) > 0,
        }

    def shutdown(self) -> dict[str, Any]:
        """Gracefully shut down SAGE platform services."""
        if self.status == "STOPPED":
            logger.warning("SAGE Service is already stopped.")
            return {"status": self.status, "message": "Service already inactive"}

        self.status = "STOPPED"
        self.session_tokens.clear()
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
            "api_keys_loaded": len(self.api_key_hashes),
        }
        return DiagnosticReport(
            status=self.status,
            uptime_seconds=uptime,
            platform_info=platform_data,
            diagnostics_passed=(self.status == "RUNNING" and len(self.api_key_hashes) > 0),
        )

    def authorize(self, api_key: str) -> bool:
        """Validate API key against loaded keys. FAIL-CLOSED.
        
        Args:
            api_key: Raw API key string from request header
            
        Returns:
            True if key is valid, False otherwise (no exceptions)
        """
        if not api_key:
            return False
        
        # Reload keys from environment (supports rotation without restart)
        self.load_api_keys_from_environment()
        
        # Hash the provided key and check against loaded hashes
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        is_valid = key_hash in self.api_key_hashes
        
        if not is_valid:
            logger.warning(f"Unauthorized API key attempt. Hash: {key_hash[:8]}...")
        
        return is_valid

    def generate_session_token(self, agent_id: str, duration_seconds: int = 3600) -> dict[str, Any]:
        """Generate a short-lived session token for an authenticated agent.
        
        Args:
            agent_id: Identifier of the agent (e.g., "ChatGPT", "agent_jules_sage")
            duration_seconds: Token validity duration (default 1 hour)
            
        Returns:
            Token data dict with ID and expiration timestamp
        """
        token_id = f"token_{int(time.time())}_{os.urandom(8).hex()}"
        created_at = time.time()
        expires_at = created_at + duration_seconds
        
        token_data = {
            "token_id": token_id,
            "agent_id": agent_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "scope": "runtime_session_access",
        }
        
        self.session_tokens[token_id] = token_data
        logger.info(f"Generated session token for agent '{agent_id}': {token_id[:16]}...")
        return token_data

    def validate_session_token(self, token_id: str) -> bool:
        """Validate a session token is valid and not expired.
        
        Args:
            token_id: Token identifier to validate
            
        Returns:
            True if token is valid and not expired, False otherwise
        """
        if token_id not in self.session_tokens:
            return False
        
        token_data = self.session_tokens[token_id]
        is_valid = time.time() < token_data["expires_at"]
        
        if not is_valid:
            # Clean up expired tokens
            del self.session_tokens[token_id]
        
        return is_valid

    def revoke_session_token(self, token_id: str) -> bool:
        """Revoke a session token (immediate logout).
        
        Args:
            token_id: Token identifier to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        if token_id in self.session_tokens:
            del self.session_tokens[token_id]
            logger.info(f"Revoked session token: {token_id[:16]}...")
            return True
        return False
