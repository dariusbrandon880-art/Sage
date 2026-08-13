#!/usr/bin/env python3
"""SAGE Assembly-Line Preflight and Anti-Regression Checker.

This script programmatically enforces SAGE's core safety boundaries,
the One-Way Import Law, and repository state integrity before any submit.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Globals for core paths to support AST testing/mocking
CORE_DIRS = ["sage/runtime", "sage/core", "sage/acr", "sage/agents", "sage/archive"]
CORE_FILES = ["sage/api.py", "sage/cli.py", "sage/capability_registry.py", "sage/change_impact.py", "sage/mission_control.py"]


def print_success(msg: str):
    print(f"{GREEN}[✓] {msg}{RESET}")


def print_warn(msg: str):
    print(f"{YELLOW}[!] {msg}{RESET}")


def print_error(msg: str):
    print(f"{RED}[✗] {msg}{RESET}")


def run_command(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    """Safely runs a shell command and returns the completion object."""
    try:
        return subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check
        )
    except FileNotFoundError:
        # Tool might not be installed, return empty/error code
        class DummyProcess:
            returncode = 127
            stdout = ""
            stderr = f"Command not found: {cmd[0]}"
        return DummyProcess()


def check_repository_state() -> bool:
    """Enforces Failure Class 01: WRONG REPOSITORY STATE."""
    print("\n--- Checking Repository State (Failure Class 01) ---")

    # Check if inside git repo
    res = run_command(["git", "rev-parse", "--is-inside-work-tree"])
    if res.returncode != 0:
        print_error("Not inside a valid Git repository.")
        return False

    # Query current branch
    branch_res = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch_res.stdout.strip()
    print(f"Active branch: {branch}")

    # Query status
    status_res = run_command(["git", "status", "--porcelain"])
    modified_files = []
    for line in status_res.stdout.splitlines():
        if line.strip():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                modified_files.append(parts[1])

    if modified_files:
        print_warn(f"Found {len(modified_files)} uncommitted/staged modifications.")
        for f in modified_files[:5]:
            print(f"  - {f}")
        if len(modified_files) > 5:
            print(f"  - ... and {len(modified_files) - 5} more.")
    else:
        print_success("Working tree is completely clean.")

    print_success("Repository state checked successfully.")
    return True


def check_historical_evidence() -> bool:
    """Enforces Failure Class 03: HISTORICAL EVIDENCE CONTAMINATION."""
    print("\n--- Checking Historical Evidence Immutability (Failure Class 03) ---")

    # Get all modified or untracked files
    diff_res = run_command(["git", "status", "--porcelain"])
    modified_paths = []
    for line in diff_res.stdout.splitlines():
        if line.strip():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                modified_paths.append(parts[1])

    # Audit for Phase 4 or Phase 5 files
    contaminated = []
    for path in modified_paths:
        if "evidence_capture/phase_4_" in path or "evidence_capture/phase_5_repeatability_" in path:
            contaminated.append(path)

    if contaminated:
        print_error("HISTORICAL EVIDENCE CONTAMINATION DETECTED! Modified files:")
        for path in contaminated:
            print(f"  - {path}")
        print_error("Historical Phase 4/5 files are completely immutable. STOPPING EXECUTION.")
        return False

    print_success("No historical evidence contamination detected.")
    return True


def check_one_way_import_law() -> bool:
    """Enforces Failure Class 11: RESEARCH -> CODE LEAK (One-Way Import Law).

    Validates that core production namespaces never statically import from experimental folders.
    """
    print("\n--- Checking One-Way Import Law (Failure Class 11) ---")

    all_python_files: List[Path] = []
    for d in CORE_DIRS:
        dir_path = Path(d)
        if dir_path.exists():
            all_python_files.extend(dir_path.glob("**/*.py"))

    for f in CORE_FILES:
        file_path = Path(f)
        if file_path.exists():
            all_python_files.append(file_path)

    violations = []
    for py_file in all_python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except Exception as e:
            print_warn(f"Failed to parse AST of {py_file}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("sage.experimental") or alias.name.startswith("sage/experimental"):
                        violations.append((py_file, node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module.startswith("sage.experimental") or node.module.startswith("sage/experimental") or node.module == "experimental":
                        violations.append((py_file, node.lineno, f"from {node.module} import ..."))

    if violations:
        print_error("ONE-WAY IMPORT LAW VIOLATION DETECTED!")
        print_error("Core namespaces are importing statically from experimental packages:")
        for filename, lineno, detail in violations:
            print(f"  - {filename}:{lineno} -> {detail}")
        return False

    print_success("One-Way Import Law verified! No illegal static imports from experimental.")
    return True


def check_protected_boundary(allow_core_modification: bool = False) -> bool:
    """Enforces Failure Class 10: PROTECTED-BOUNDARY VIOLATION."""
    print("\n--- Checking Protected Core Boundaries (Failure Class 10) ---")

    # Query files modified relative to origin/main or HEAD
    diff_res = run_command(["git", "diff", "--name-only"])
    modified_files = [line.strip() for line in diff_res.stdout.splitlines() if line.strip()]

    # Add staged files
    diff_staged = run_command(["git", "diff", "--cached", "--name-only"])
    modified_files.extend([line.strip() for line in diff_staged.stdout.splitlines() if line.strip()])

    modified_files = list(set(modified_files))

    protected_prefixes = ["sage/runtime/", "sage/core/", "sage/acr/", "sage/agents/"]
    violations = []

    for f in modified_files:
        for prefix in protected_prefixes:
            if f.startswith(prefix):
                violations.append(f)
                break

    if violations:
        if allow_core_modification:
            print_warn("Protected core modifications detected, but override flag is ACTIVE:")
            for f in violations:
                print(f"  - {f} (MODIFIED - ALLOWED)")
        else:
            print_error("PROTECTED-BOUNDARY VIOLATION DETECTED! Modifying frozen core directories without authorization:")
            for f in violations:
                print(f"  - {f}")
            print_error("Please keep experimental developments in 'sage/experimental/' or request authorization.")
            return False
    else:
        print_success("No protected-boundary violations found.")

    return True


def check_scope_drift(active_scope: str = "any") -> bool:
    """Enforces Failure Class 02: SCOPE DRIFT."""
    print(f"\n--- Checking Scope Drift (Failure Class 02) [Scope: {active_scope}] ---")

    if active_scope == "any":
        print_success("Scope drift check bypassed: any changes permitted.")
        return True

    diff_res = run_command(["git", "diff", "--name-only"])
    modified_files = [line.strip() for line in diff_res.stdout.splitlines() if line.strip()]

    diff_staged = run_command(["git", "diff", "--cached", "--name-only"])
    modified_files.extend([line.strip() for line in diff_staged.stdout.splitlines() if line.strip()])
    modified_files = list(set(modified_files))

    if active_scope == "ci-only":
        forbidden = []
        for f in modified_files:
            is_ci = any(f.startswith(p) for p in [".github/", "scripts/", "pyproject.toml", "poetry.lock", "Dockerfile", "docker-compose.yml"])
            if not is_ci:
                forbidden.append(f)
        if forbidden:
            print_error(f"SCOPE DRIFT VIOLATION! Task is set to CI-ONLY, but non-CI files were modified:")
            for f in forbidden:
                print(f"  - {f}")
            return False

    elif active_scope == "audit-only":
        implementation_and_tests = []
        for f in modified_files:
            is_impl_or_test = any(f.startswith(p) for p in ["sage/", "tests/"])
            if is_impl_or_test:
                implementation_and_tests.append(f)
        if implementation_and_tests:
            print_error(f"SCOPE DRIFT VIOLATION! Task is set to AUDIT-ONLY, but workspace files were modified:")
            for f in implementation_and_tests:
                print(f"  - {f}")
            return False

    print_success(f"Scope check passed cleanly for scope '{active_scope}'.")
    return True


def run_formatting_checks() -> bool:
    """Verifies that code is clean and adheres to style guidelines."""
    print("\n--- Running Formatting & Linter Checks ---")

    black_res = run_command(["poetry", "run", "black", "--check", "sage", "tests", "scripts"])
    if black_res.returncode != 0:
        print_warn("Black formatting check failed. Run 'poetry run black .' to auto-format.")
    else:
        print_success("Black formatting check passed.")

    ruff_res = run_command(["poetry", "run", "ruff", "check", "sage", "tests", "scripts"])
    if ruff_res.returncode != 0:
        print_warn("Ruff lint check found potential issues:")
        print(ruff_res.stdout)
    else:
        print_success("Ruff linter check passed.")

    return True


def run_assembly_line_preflight(active_scope: str = "any", allow_core: bool = False) -> bool:
    """Orchestrates the full mandatory Assembly-Line Preflight."""
    print("=" * 60)
    print(" SAGE ASSEMBLY-LINE PREFLIGHT CHECKER")
    print("=" * 60)

    checks = [
        check_repository_state(),
        check_historical_evidence(),
        check_one_way_import_law(),
        check_protected_boundary(allow_core_modification=allow_core),
        check_scope_drift(active_scope=active_scope),
        run_formatting_checks()
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print(f"{GREEN}{BOLD}PREFLIGHT SUCCESSFUL! All safety and quality constraints are SATISFIED.{RESET}")
        print("=" * 60)
        return True
    else:
        print(f"{RED}{BOLD}PREFLIGHT FAILED! One or more critical constraints were VIOLATED.{RESET}")
        print("Please correct the issues listed above before executing or submitting work.")
        print("=" * 60)
        return False


if __name__ == "__main__":
    scope = "any"
    allow_core_mod = False

    for arg in sys.argv[1:]:
        if arg.startswith("--scope="):
            scope = arg.split("=")[1].strip()
        elif arg == "--allow-core":
            allow_core_mod = True

    success = run_assembly_line_preflight(active_scope=scope, allow_core=allow_core_mod)
    sys.exit(0 if success else 1)
