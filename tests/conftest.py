"""Test utilities and fixtures for SAGE tests."""

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from sage.archive import Archive
from sage.decision import DecisionTracker
from sage.memory import MemoryStore
from sage.runtime import SAGERuntime
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


if os.environ.get("SAGE_CI_OPENAI_STUB") == "1":
    class _Responses:
        def create(self, *, model, instructions, input):
            return SimpleNamespace(output_text=f"CI stub response for: {input}")

    class _Client:
        def __init__(self, api_key=None):
            self.responses = _Responses()

    sys.modules.setdefault("openai", SimpleNamespace(OpenAI=_Client))
