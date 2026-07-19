"""Test utilities and fixtures for SAGE tests."""

import pytest
import tempfile
from pathlib import Path

from sage.runtime import SAGERuntime
from sage.memory import MemoryStore
from sage.archive import Archive
from sage.decision import DecisionTracker
from sage.validation import ValidationSystem


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def runtime(temp_workspace):
    """Create a test runtime instance."""
    return SAGERuntime(str(temp_workspace))


@pytest.fixture
def memory_store(temp_workspace):
    """Create a test memory store."""
    return MemoryStore(str(temp_workspace / "memory"))


@pytest.fixture
def archive(temp_workspace):
    """Create a test archive."""
    return Archive(str(temp_workspace / "archive"))


@pytest.fixture
def decision_tracker(temp_workspace):
    """Create a test decision tracker."""
    return DecisionTracker(str(temp_workspace / "decisions"))


@pytest.fixture
def validation_system(memory_store, archive):
    """Create a test validation system."""
    return ValidationSystem(memory_store, archive)
