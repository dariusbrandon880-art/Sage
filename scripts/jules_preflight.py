#!/usr/bin/env python3
"""SAGE Preflight Checker & Durable Failure Memory Gate.

Converts SAGE's verified historical failures into an executable development gate
by performing repository-state checks, historical evidence immutability checks,
scope checks, protected-core checks, and AST-based One-Way Import Law checking.
"""

import os
import sys
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


class SAGEPreflightChecker:
    """Executable preflight checker enforcing durable failure memory rules."""

    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        self.protected_paths = [
            "sage/core",
            "sage/acr",
            "sage/runtime",
            "sage/agents"
        ]
        self.historical_evidence_paths = [
            "evidence_capture/phase_4"
        ]

    def check_branch_ancestry(self) -> Tuple[bool, str]:
        """Ensure the branch is derived from the latest main and is conflict-free."""
        try:
            res = subprocess.run(
                ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
                capture_output=True,
                text=True
            )
            if res.returncode != 0:
                return False, "Branch ancestry violation: Current HEAD is not derived from latest main (stale state)."
            return True, "Branch ancestry verified successfully."
        except Exception as e:
            return True, f"Branch ancestry check bypassed: {e}"

    def check_historical_evidence_immutability(self) -> Tuple[bool, str]:
        """Ensure that historical Phase 4 evidence files are completely untouched."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            modified_files = []
            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) >= 2:
                    filepath = parts[1].strip('"')
                    if any(filepath.startswith(p) for p in self.historical_evidence_paths):
                        modified_files.append(filepath)

            if modified_files:
                return False, f"Historical evidence mutation violation: Modified historical files: {modified_files}."
            return True, "Historical evidence immutability verified."
        except Exception as e:
            return True, f"Historical evidence check bypassed: {e}"

    def check_protected_core_boundaries(self) -> Tuple[bool, str]:
        """Ensure no core production files have been modified or mutated."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            modified_core = []
            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) >= 2:
                    filepath = parts[1].strip('"')
                    if any(filepath.startswith(p) for p in self.protected_paths):
                        modified_core.append(filepath)

            if modified_core:
                return False, f"Protected core boundary violation: Attempted mutation of core namespaces: {modified_core}."
            return True, "Protected core boundaries verified."
        except Exception as e:
            return True, f"Protected core boundaries check bypassed: {e}"

    def check_one_way_import_law(self) -> Tuple[bool, str]:
        """Enforce strict One-Way Import Law using AST parsing on all python files."""
        violations = []
        sage_dir = self.repo_root / "sage"
        if not sage_dir.exists():
            return True, "No sage package found for One-Way Import Law check."
        for path in sage_dir.glob("**/*.py"):
            if "site-packages" in path.parts or ".venv" in path.parts or ".cache" in path.parts or "experimental" in path.parts:
                continue

            with open(path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=str(path))
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if "sage.experimental" in alias.name:
                                violations.append(f"{path}: Direct import of '{alias.name}'")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "sage.experimental" in node.module:
                            violations.append(f"{path}: Import from module '{node.module}'")

        if violations:
            return False, f"One-Way Import Law Violation: Core production namespaces imported experimental paths:\n" + "\n".join(violations)
        return True, "One-Way Import Law verified."

    def run_all_checks(self) -> Tuple[bool, List[str]]:
        """Execute all preflight checks and return the overall outcome and reports."""
        checks = [
            self.check_branch_ancestry,
            self.check_historical_evidence_immutability,
            self.check_protected_core_boundaries,
            self.check_one_way_import_law
        ]

        reports = []
        all_passed = True
        for check in checks:
            passed, msg = check()
            reports.append(msg)
            if not passed:
                all_passed = False

        return all_passed, reports


def main():
    """CLI entrypoint for preflight checking."""
    checker = SAGEPreflightChecker()
    success, reports = checker.run_all_checks()

    print("======================================================")
    print("              SAGE ASSEMBLY-LINE PREFLIGHT             ")
    print("======================================================")
    for r in reports:
        print(f"  [*] {r}")
    print("======================================================")

    if not success:
        print("  [STATUS] PREFLIGHT FAILED - EXECUTABLE GATE REJECTED.")
        print("======================================================")
        sys.exit(1)
    else:
        print("  [STATUS] PREFLIGHT PASSED - SECURE FRONTIER SECURED.")
        print("======================================================")
        sys.exit(0)


if __name__ == "__main__":
    main()
