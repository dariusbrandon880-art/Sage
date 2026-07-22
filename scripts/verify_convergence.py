#!/usr/bin/env python
"""SAGE Automated Milestone & Merge Convergence Verification Script.

This utility automates the verification checks specified in the SAGE Merge
Convergence Policy to guarantee repository and runtime integrity before merging.
"""

import sys
import subprocess
from pathlib import Path

# ANSI colors for beautiful output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(name: str):
    print(f"\n{BLUE}=== Step: {name} ==={RESET}")


def run_command(command: list[str], description: str) -> bool:
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"{GREEN}✓ {description} passed.{RESET}")
            return True
        else:
            print(f"{RED}✗ {description} failed.{RESET}")
            print(f"{YELLOW}Standard Output:{RESET}\n{result.stdout}")
            print(f"{RED}Standard Error:{RESET}\n{result.stderr}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error executing command: {e}{RESET}")
        return False


def verify_environment() -> bool:
    print_step("Python Environment & SAGE Package Installation")
    try:
        import sage  # noqa: F401
        from sage.runtime import SageRuntime  # noqa: F401

        print(f"{GREEN}✓ SAGE package import check passed.{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}✗ SAGE package is not installable or importable: {e}{RESET}")
        print(f"{YELLOW}Hint: Run 'pip install -e \".[dev]\"' in the repository root.{RESET}")
        return False


def verify_pytest() -> bool:
    print_step("Pytest Suite Execution")
    return run_command(["python", "-m", "pytest"], "Unit and integration tests")


def verify_ruff() -> bool:
    print_step("Ruff Linting Rules")
    return run_command(["ruff", "check", "."], "Ruff code style checking")


def verify_black() -> bool:
    print_step("Black Code Formatting")
    return run_command(["black", "--check", "."], "Black formatting consistency")


def verify_runtime_status() -> bool:
    print_step("SAGE Runtime Diagnostics")
    try:
        from sage.runtime import SageRuntime

        runtime = SageRuntime()
        status = runtime.get_status()
        print(f"Runtime Status details: {status}")
        if status.get("active") is not None:
            print(f"{GREEN}✓ SAGE Runtime instantiated and returned valid status.{RESET}")
            return True
        else:
            print(f"{RED}✗ Runtime status is missing expected fields.{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Failed to instantiate or query SAGE Runtime: {e}{RESET}")
        return False


def verify_cli_status() -> bool:
    print_step("SAGE CLI Integration")
    return run_command(["python", "-m", "sage.cli", "status"], "SAGE CLI 'status' command")


def verify_documentation_integrity() -> bool:
    print_step("Documentation and State Files Integrity")
    required_docs = [
        "docs/master/MASTER_SNAPSHOT.md",
        "docs/master/SESSION_STATE.md",
        "docs/master/MERGE_CONVERGENCE_POLICY.md",
        "docs/master/FINAL_ACTIVATION_REPORT.md",
    ]
    all_exist = True
    for doc in required_docs:
        path = Path(doc)
        if path.exists() and path.is_file():
            print(f"{GREEN}✓ Operational document exists: {doc}{RESET}")
        else:
            print(f"{RED}✗ Required operational document is missing or not a file: {doc}{RESET}")
            all_exist = False
    return all_exist


def verify_archive_integrity() -> bool:
    print_step("Master Archive Registry Integrity")
    index_path = Path("Main Archive/INDEX.md")
    if not index_path.exists() or not index_path.is_file():
        print(f"{RED}✗ Master Archive Index is missing: Main Archive/INDEX.md{RESET}")
        return False

    print(f"{GREEN}✓ Master Archive Index exists: {index_path}{RESET}")

    # Read the index and check if all relative markdown links exist
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re

    # Match markdown links of form [Name](path.md)
    links = re.findall(r"\[.*?\]\((.*?\.md)\)", content)
    if not links:
        print(f"{YELLOW}Warning: No markdown files linked in {index_path}{RESET}")
        return True

    print(f"Found {len(links)} cataloged links inside Master Archive Index.")
    all_links_exist = True
    for link in links:
        # Resolve path relative to Main Archive/ directory
        full_path = Path("Main Archive") / link
        if full_path.exists() and full_path.is_file():
            print(f"  {GREEN}✓ Linked document exists: {link}{RESET}")
        else:
            print(f"  {RED}✗ Linked document is missing: {link} (Resolved: {full_path}){RESET}")
            all_links_exist = False

    return all_links_exist


def main():
    print(f"{BLUE}====================================================={RESET}")
    print(f"{BLUE}        SAGE MERGE CONVERGENCE VERIFICATION          {RESET}")
    print(f"{BLUE}====================================================={RESET}")

    steps = [
        ("Environment Check", verify_environment),
        ("Pytest Execution", verify_pytest),
        ("Ruff Check", verify_ruff),
        ("Black Check", verify_black),
        ("Runtime Diagnostics", verify_runtime_status),
        ("CLI Diagnostics", verify_cli_status),
        ("Documentation Integrity", verify_documentation_integrity),
        ("Master Archive Integrity", verify_archive_integrity),
    ]

    failed_steps = []
    for name, step_func in steps:
        try:
            success = step_func()
            if not success:
                failed_steps.append(name)
        except Exception as e:
            print(f"{RED}✗ Exception occurred in check '{name}': {e}{RESET}")
            failed_steps.append(name)

    print(f"\n{BLUE}====================================================={RESET}")
    print(f"{BLUE}                 VERIFICATION SUMMARY                {RESET}")
    print(f"{BLUE}====================================================={RESET}")

    if not failed_steps:
        print(f"{GREEN}✓ All checks passed successfully!{RESET}")
        print(f"{GREEN}This workspace is fully aligned and ready for merge convergence.{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}✗ SAGE verification failed on steps: {', '.join(failed_steps)}{RESET}")
        print(
            f"{RED}Please resolve all style, test, and documentation issues before merging.{RESET}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
