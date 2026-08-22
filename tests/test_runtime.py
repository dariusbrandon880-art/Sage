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

    def test_runtime_c2_bootstrap_contract(self):
        """Test runtime initializes and exposes C2Bootstrap control contract."""
        runtime = SageRuntime()
        assert hasattr(runtime, "c2_bootstrap")
        assert hasattr(runtime, "c2_boot_result")
        assert runtime.c2_boot_result.rehydrated is True
        assert runtime.c2_boot_result.execution_surface_checked is True
        assert runtime.c2_boot_result.direct_execution_available is True

        status = runtime.get_status()
        assert "c2_status" in status
        assert status["c2_status"]["rehydrated"] is True
        assert status["c2_status"]["direct_execution_available"] is True
