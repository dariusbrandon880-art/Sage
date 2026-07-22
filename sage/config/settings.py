"""SAGE runtime configuration management."""

from typing import Optional
from pydantic_settings import BaseSettings


class SageConfig(BaseSettings):
    """Configuration for SAGE runtime."""

    # Runtime settings
    debug: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    env: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"

    # Storage settings
    memory_backend: str = "in-memory"
    archive_backend: str = "in-memory"

    # ACR settings
    enable_continuity: bool = True
    continuity_timeout: int = 3600  # seconds

    # Security settings
    sage_api_keys: str = "sage-default-key-2026"
    sage_require_auth: bool = False
    github_webhook_secret: Optional[str] = None
    github_access_token: Optional[str] = None

    # Google Workspace Synchronization
    google_workspace_credentials_path: Optional[str] = ".sage/credentials.json"

    # Gemini / Jules Agent Settings
    gemini_api_key: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @classmethod
    def from_env(cls) -> "SageConfig":
        """Load configuration from environment variables.

        Returns:
            SageConfig instance.
        """
        return cls()
