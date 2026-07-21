"""Tests for SAGE runtime engine."""

from sage.runtime import SageRuntime


class TestSageRuntime:
    """Test cases for SageRuntime."""

    def test_runtime_initialization(self):
        """Test runtime initializes correctly."""
        runtime = SageRuntime()
        assert runtime is not None
        assert not runtime.is_running()

    def test_runtime_start_stop(self):
        """Test runtime start and stop."""
        runtime = SageRuntime()
        assert not runtime.is_running()
        
        runtime.start()
        assert runtime.is_running()
        
        runtime.stop()
        assert not runtime.is_running()

    def test_runtime_with_config(self):
        """Test runtime initialization with config."""
        config = {"debug": True, "max_retries": 5}
        runtime = SageRuntime(config=config)
        assert runtime.config == config
