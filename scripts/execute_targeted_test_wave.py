#!/usr/bin/env python3
"""Runner script executing SAGE Dynamic Targeted Test Orchestration Wave."""

import json
import subprocess
import sys
from pathlib import Path

from sage.c2.targeted_test_executor import TargetedTestExecutor


def get_git_head() -> str:
    """Returns exact 40-character commit SHA for active HEAD."""
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def main() -> int:
    exact_head = get_git_head()
    print(f"[+] Active Git Commit HEAD: {exact_head}")

    executor = TargetedTestExecutor()

    wave_id = "targeted_test_wave_001"
    modified_files = ["tests/test_continuity_persistence.py"]

    print(f"[+] Executing Dynamic Targeted Test Wave: {wave_id} for modified files: {modified_files}")

    receipt = executor.execute_targeted_tests(
        modified_files=modified_files,
        exact_git_head=exact_head,
        wave_id=wave_id,
    )

    print(f"[+] Receipt Hash: {receipt.receipt_hash}")
    print(f"[+] Modified Files: {receipt.modified_files}")
    print(f"[+] Selected Test Files: {receipt.selected_test_files}")
    print(f"[+] Fallback to Full Suite: {receipt.fallback_to_full_suite}")
    print(f"[+] Tests Executed: {receipt.tests_executed}, Passed: {receipt.tests_passed}, Failed: {receipt.tests_failed}")
    print(f"[+] Execution Time: {receipt.execution_time_seconds:.3f}s")
    print(f"[+] Verdict: {receipt.verdict}")

    if receipt.verdict != "PASS":
        print("[!] ERROR: Targeted Test Wave failed!", file=sys.stderr)
        return 1

    evidence_path = Path("evidence_capture/targeted_test_wave_evidence.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(receipt.model_dump(), f, indent=2)

    print(f"[+] Successfully persisted evidence receipt to {evidence_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
