"""Tests for SAGE Capability Registry."""

import pytest
from sage.registry.models import Capability
from sage.registry.core import CapabilityRegistry


def test_capability_registration_and_retrieval():
    """Test registering, listing, and retrieving capabilities."""
    registry = CapabilityRegistry()
    cap = Capability(
        id="run_diagnostic",
        name="System Diagnostics",
        description="Run local system hardware and software diagnostics",
        permissions=["admin"],
    )

    registry.register_capability(cap)

    retrieved = registry.retrieve_capability("run_diagnostic")
    assert retrieved is not None
    assert retrieved.name == "System Diagnostics"
    assert "admin" in retrieved.permissions

    caps = registry.list_capabilities()
    assert len(caps) == 1
    assert caps[0].id == "run_diagnostic"


def test_capability_invocation_success():
    """Test successful dynamic capability invocation."""
    registry = CapabilityRegistry()
    cap = Capability(
        id="add_numbers",
        name="Addition Service",
        description="Adds two integers together",
        permissions=["math"],
    )

    def add_handler(a: int, b: int) -> int:
        return a + b

    registry.register_capability(cap, handler=add_handler)

    result = registry.invoke_capability("add_numbers", {"a": 10, "b": 25}, scopes=["math"])
    assert result == 35


def test_capability_invocation_failures():
    """Test capability invocation failure cases (missing scopes, missing cap, inactive)."""
    registry = CapabilityRegistry()
    cap = Capability(
        id="secure_delete",
        name="Secure File Removal",
        description="Permanently deletes a workspace file",
        permissions=["dangerous"],
        active=True,
    )

    registry.register_capability(cap, lambda: "deleted")

    # 1. Missing permission scope
    with pytest.raises(PermissionError):
        registry.invoke_capability("secure_delete", {}, scopes=["read"])

    # 2. Inactive capability
    cap.active = False
    with pytest.raises(ValueError):
        registry.invoke_capability("secure_delete", {}, scopes=["dangerous"])

    # 3. Missing capability ID
    with pytest.raises(ValueError):
        registry.invoke_capability("nonexistent", {}, scopes=["dangerous"])
