"""Tests for SAGE configuration."""

from sage.config import SageConfig


class TestSageConfig:
    """Test cases for SageConfig."""

    def test_config_defaults(self):
        """Test configuration defaults."""
        config = SageConfig()
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.max_retries == 3
        assert config.enable_continuity is True

    def test_config_initialization(self):
        """Test configuration with custom values."""
        config = SageConfig(
            debug=True,
            log_level="DEBUG",
            max_retries=5,
        )
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
