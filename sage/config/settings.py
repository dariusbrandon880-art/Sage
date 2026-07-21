"""SAGE runtime configuration management."""

from pydantic_settings import BaseSettings


class SageConfig(BaseSettings):
    """Configuration for SAGE runtime."""

    # Runtime settings
    debug: bool = False
    log_level: str = "INFO"
    max_retries: int = 3

    # Storage settings
    memory_backend: str = "in-memory"
    archive_backend: str = "in-memory"

    # ACR settings
    enable_continuity: bool = True
    continuity_timeout: int = 3600  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "SageConfig":
        """Load configuration from environment variables.
        
        Returns:
            SageConfig instance.
        """
        return cls()
