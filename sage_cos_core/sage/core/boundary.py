"""SAGE SPEK Security Boundary Enforcement."""

import os
from pathlib import Path


class BoundaryEnforcer:
    """Enforces strict path isolation and write-boundary checks.

    Protects 'sage/core' and '.sage' paths from unauthorized outside mutations.
    """

    def __init__(self, root_dir: str | Path | None = None):
        """Initialize boundary enforcer."""
        self.root_dir = Path(root_dir or ".").resolve()

        # Protected folders (resolved relative to root)
        self.protected_subpaths = [
            Path("sage_cos_core/sage/core"),
            Path("sage_cos_core/.sage"),
            Path("sage/core"),
            Path(".sage"),
        ]

    def is_protected_path(self, target_path: str | Path) -> bool:
        """Check if a path falls inside any of the protected system directories."""
        try:
            resolved_target = Path(target_path).resolve()
        except Exception:
            # Fallback to absolute check if resolve fails
            resolved_target = Path(target_path).absolute()

        for subpath in self.protected_subpaths:
            resolved_protected = (self.root_dir / subpath).resolve()
            # Check if resolved_target is equal to or a subpath of resolved_protected
            try:
                if resolved_target == resolved_protected or resolved_protected in resolved_target.parents:
                    return True
            except Exception:
                pass

        return False

    def validate_write_permission(self, target_path: str | Path, caller_auth_token: str | None = None) -> None:
        """Validate write permission to the target path.

        Raises:
            PermissionError: If writing to a protected path without the system's authorized token.
        """
        if self.is_protected_path(target_path):
            # Authorize only if the correct internally derived token is supplied
            # In a production environment, this is derived from spek's system credentials
            expected_token = os.getenv("SAGE_SPEK_SYSTEM_TOKEN") or "spek_system_internal_auth_token_2026"
            if caller_auth_token != expected_token:
                raise PermissionError(
                    f"BOUNDARY ISOLATION VIOLATION: Unauthorized mutation attempt to protected path: {target_path}"
                )
