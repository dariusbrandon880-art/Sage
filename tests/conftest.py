"""Pytest configuration and fixtures for SAGE test suite."""

import pytest
from sage.runtime import SageRuntime
from sage.memory import MemoryStore
from sage.archive import ArchiveLog
from sage.acr import ACRBridge
from sage.config import SageConfig


@pytest.fixture
def runtime():
    """Fixture providing a SageRuntime instance."""
    return SageRuntime()


@pytest.fixture
def memory_store():
    """Fixture providing a MemoryStore instance."""
    return MemoryStore()


@pytest.fixture
def archive_log():
    """Fixture providing an ArchiveLog instance."""
    return ArchiveLog()


@pytest.fixture
def acr_bridge():
    """Fixture providing an ACRBridge instance."""
    return ACRBridge()


@pytest.fixture
def sage_config():
    """Fixture providing a SageConfig instance."""
    return SageConfig()
