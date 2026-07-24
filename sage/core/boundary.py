"""Security Boundary Enforcement for SAGE core, validation, and governance contracts."""

import os
from pathlib import Path
from typing import Optional, Set


class BoundaryEnforcer:
    """Enforces execution and state path isolation for SAGE's core platform boundaries.

    Ensures that only authorized processes and systems with a valid system token
    can write to or mutate critical SAGE governance/core directories and files.
    """

    SYSTEM_TOKEN = "SECURE_SPEK_SYSTEM_TOKEN_2026"

    def __init__(self, protected_directories: Optional[Set[str]] = None, protected_files: Optional[Set[str]] = None):
        """Initialize BoundaryEnforcer.

        Args:
            protected_directories: Optional custom set of directory names/paths to protect.
            protected_files: Optional custom set of filenames/paths to protect.
        """
        # Define default protected areas
        self.protected_directories = protected_directories or {
            "sage/core",
            ".sage/validation",
        }
        self.protected_files = protected_files or {
            "docs/master/CONSTITUTION.md",
            "docs/master/ROADMAP.md",
            ".sage/ROADMAP.md"
        }

    def is_protected(self, path: str | Path) -> bool:
        """Check if a given path falls within the protected SAGE boundaries.

        Args:
            path: Target path to check.

        Returns:
            True if path is in a protected directory or matches a protected file.
        """
        resolved = Path(path).resolve()
        repo_root = Path(os.getcwd()).resolve()

        # Check files
        for protected_file in self.protected_files:
            file_abs = (repo_root / protected_file).resolve()
            if resolved == file_abs:
                return True

        # Check directories
        for protected_dir in self.protected_directories:
            dir_abs = (repo_root / protected_dir).resolve()
            try:
                # If resolved path is equal to or subpath of protected directory
                if resolved == dir_abs or dir_abs in resolved.parents:
                    return True
            except ValueError:
                pass

        return False

    def validate_mutation(self, path: str | Path, auth_token: Optional[str] = None) -> None:
        """Validate if a mutation (write/delete) to a path is authorized.

        Args:
            path: Target path being mutated.
            auth_token: Present security token.

        Raises:
            PermissionError: If path is protected and token is invalid or missing.
        """
        if self.is_protected(path):
            if auth_token != self.SYSTEM_TOKEN:
                raise PermissionError(
                    f"Security Boundary Enforcement Violation: Unauthorized mutation attempt "
                    f"on protected path: {path}. Execution blocked."
                )
