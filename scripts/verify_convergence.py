#!/usr/bin/env python3
"""Automated Merge Convergence and Milestone Validation Script for SAGE."""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run a system command and return the completed process object."""
    return subprocess.run(cmd, capture_output=True, text=True)


def check_linting() -> Dict[str, Any]:
    """Check code linting using Ruff."""
    proc = run_command(["ruff", "check", "sage/", "tests/", "scripts/"])
    return {"passed": proc.returncode == 0, "output": proc.stdout + proc.stderr}


def check_formatting() -> Dict[str, Any]:
    """Check formatting using Black."""
    proc = run_command(["black", "--check", "sage/", "tests/", "scripts/"])
    return {"passed": proc.returncode == 0, "output": proc.stdout + proc.stderr}


def run_tests() -> Dict[str, Any]:
    """Run full test suite via pytest."""
    proc = run_command(["python", "-m", "pytest"])
    return {"passed": proc.returncode == 0, "output": proc.stdout + proc.stderr}


def scan_for_merge_conflict_markers() -> Dict[str, Any]:
    """Scan all markdown files in docs/master/ for git merge conflict markers."""
    docs_dir = Path("docs/master")
    conflict_files = []
    conflict_markers = ["<<<<<<<", "=======", ">>>>>>>"]

    if docs_dir.exists():
        for p in docs_dir.glob("**/*.md"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                if any(marker in content for marker in conflict_markers):
                    conflict_files.append(str(p))
            except Exception:
                pass

    return {"passed": len(conflict_files) == 0, "files": conflict_files}


def check_repo_cleanliness() -> Dict[str, Any]:
    """Check repository root for unintended temporary files (e.g., sage_data leftover)."""
    root_paths = list(Path(".").glob("*"))
    unintended = []
    forbidden_names = ["sage_data", "test_workspace", "tmp", "temp_workspace"]

    for p in root_paths:
        if p.name in forbidden_names:
            unintended.append(str(p))

    return {"passed": len(unintended) == 0, "unintended_files": unintended}


def main():
    print("======================================================================")
    print(" SAGE AUTOMATED MERGE CONVERGENCE & WORKFLOW VALIDATION")
    print("======================================================================\n")

    steps_failed = 0

    # 1. Ruff Lint check
    print("[1/5] Running Ruff code linter check...")
    lint_res = check_linting()
    if lint_res["passed"]:
        print("  - SUCCESS: SAGE python code conforms 100% to Ruff lint standards.")
    else:
        print("  - FAILURE: Ruff linting detected issues:")
        print(lint_res["output"])
        steps_failed += 1

    # 2. Black Formatting check
    print("\n[2/5] Running Black formatting style check...")
    format_res = check_formatting()
    if format_res["passed"]:
        print("  - SUCCESS: SAGE python code conforms 100% to Black style guidelines.")
    else:
        print(
            "  - FAILURE: Black formatting check failed. Run 'black sage/ tests/ scripts/' to fix."
        )
        print(format_res["output"])
        steps_failed += 1

    # 3. Pytest test suite check
    print("\n[3/5] Running automated pytest test suite...")
    test_res = run_tests()
    if test_res["passed"]:
        print("  - SUCCESS: All automated test suites passed successfully.")
    else:
        print("  - FAILURE: Test suite failures detected:")
        print(test_res["output"])
        steps_failed += 1

    # 4. Merge conflict marker scan
    print("\n[4/5] Scanning state documentation for git merge conflict markers...")
    conflict_res = scan_for_merge_conflict_markers()
    if conflict_res["passed"]:
        print("  - SUCCESS: No git merge conflict markers found in docs/master/.")
    else:
        print("  - FAILURE: Found git merge conflict markers in following files:")
        for f in conflict_res["files"]:
            print(f"    * {f}")
        steps_failed += 1

    # 5. Repo cleanliness check
    print("\n[5/5] Checking repository root cleanliness...")
    clean_res = check_repo_cleanliness()
    if clean_res["passed"]:
        print("  - SUCCESS: Repository root directory is clean of temporary test databases.")
    else:
        print("  - WARNING: Found unintended temporary paths at repository root:")
        for f in clean_res["unintended_files"]:
            print(f"    * {f}")
        print("    (Recommendation: Delete these paths to avoid committing local run artifacts.)")

    print("\n======================================================================")
    if steps_failed == 0:
        print(" CONVERGENCE STATUS: SAGE MILESTONE VALIDATED (100% CONVERGED)")
        print(" All quality gates, linter rules, formatters, and test gates are GREEN.")
        print("======================================================================")
        sys.exit(0)
    else:
        print(f" CONVERGENCE STATUS: FAILED ({steps_failed} gate(s) failed)")
        print(" Please resolve the failures before merging or finalizing the sprint.")
        print("======================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
