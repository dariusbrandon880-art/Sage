"""SAGE SPEK Security Boundary Enforcement Tests."""

import pytest
from pathlib import Path

from sage_cos_core.sage.core.boundary import BoundaryEnforcer


def test_boundary_path_protection():
    """Test 6: Protected path mutation attempt.

    Expected: permission failure.
    """
    enforcer = BoundaryEnforcer()

    # Verify that paths under 'sage_cos_core/sage/core' and '.sage' are identified as protected
    assert enforcer.is_protected_path("sage_cos_core/sage/core/spek.py") is True
    assert enforcer.is_protected_path("sage_cos_core/.sage/validation/audit/spek_vault.json") is True
    assert enforcer.is_protected_path("sage/core/spek.py") is True
    assert enforcer.is_protected_path(".sage/validation/audit/spek_vault.json") is True

    # Unprotected pathways are allowed
    assert enforcer.is_protected_path("unprotected_folder/logs.txt") is False

    # Validation should allow writes with correct internal token
    valid_token = "spek_system_internal_auth_token_2026"
    enforcer.validate_write_permission("sage_cos_core/.sage/spek_vault.json", valid_token)

    # Validation must raise PermissionError for unauthorized access
    invalid_token = "outside_ai_token_123"
    with pytest.raises(PermissionError, match="BOUNDARY ISOLATION VIOLATION"):
        enforcer.validate_write_permission("sage_cos_core/.sage/spek_vault.json", invalid_token)

    with pytest.raises(PermissionError, match="BOUNDARY ISOLATION VIOLATION"):
        enforcer.validate_write_permission("sage_cos_core/sage/core/spek.py", None)
