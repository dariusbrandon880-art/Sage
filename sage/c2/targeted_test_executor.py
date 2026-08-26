"""SAGE Dynamic Targeted Test Orchestrator.

Operationalizes SAGEChangeImpactAnalyzer to run change-impact-driven targeted test suites:
- Analyzes workspace modifications against SAGE Operational Capability Registry.
- Maps modified files to affected capability validation test references.
- Enforces negative-path ambiguity fallback: falls back to full test suite if UNKNOWN_DEPENDENCY or empty test set is detected.
- Measures execution time and generates cryptographically signed TargetedTestExecutionReceipt records bound to exact commit HEAD.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from sage.change_impact import SAGEChangeImpactAnalyzer


class TargetedTestExecutionReceipt(BaseModel):
    """Cryptographic evidence receipt for a targeted test execution event."""
    receipt_id: str
    wave_id: str
    exact_git_head: str
    modified_files: List[str] = Field(default_factory=list)
    selected_test_files: List[str] = Field(default_factory=list)
    fallback_to_full_suite: bool = False
    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    execution_time_seconds: float = 0.0
    verdict: str = "PASS"  # "PASS" or "FAIL"
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        files_str = ",".join(sorted(self.selected_test_files))
        payload = (
            f"{self.receipt_id}:{self.wave_id}:{self.exact_git_head}:{files_str}:"
            f"{self.fallback_to_full_suite}:{self.tests_executed}:{self.tests_passed}:"
            f"{self.tests_failed}:{self.execution_time_seconds:.3f}:{self.verdict}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TargetedTestExecutor:
    """Orchestrator mapping workspace modifications to targeted test suites."""

    def __init__(self, analyzer: Optional[SAGEChangeImpactAnalyzer] = None):
        self.analyzer = analyzer or SAGEChangeImpactAnalyzer()

    def select_tests_for_changes(self, modified_files: List[str]) -> Tuple[List[str], bool]:
        """Maps modified workspace files to target test files using change-impact analysis.

        Returns (selected_test_files, fallback_to_full_suite).
        Falls back to full suite if UNKNOWN_DEPENDENCY classification is encountered
        or if no specific test references matched.
        """
        if not modified_files:
            return (["tests/"], True)

        report = self.analyzer.analyze_changes(modified_files)

        selected_tests: set[str] = set()
        fallback_required = False

        for cap_impact in report.impacted_capabilities:
            if cap_impact.classification == "UNKNOWN_DEPENDENCY":
                fallback_required = True
            elif cap_impact.classification == "REVALIDATION_REQUIRED":
                for test_ref in cap_impact.test_references:
                    selected_tests.add(test_ref)

        test_list = sorted(list(selected_tests))

        if fallback_required or not test_list:
            return (["tests/"], True)

        return (test_list, False)

    def execute_targeted_tests(
        self,
        modified_files: List[str],
        exact_git_head: str,
        wave_id: str = "targeted_test_wave_001",
    ) -> TargetedTestExecutionReceipt:
        """Executes selected targeted test suite and generates a signed evidence receipt."""
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
        if not sha_pattern.match(exact_git_head):
            raise ValueError(f"Invalid exact git HEAD commit SHA: {exact_git_head}")

        selected_tests, is_fallback = self.select_tests_for_changes(modified_files)

        start_time = time.time()

        cmd = ["poetry", "run", "pytest", *selected_tests]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        elapsed = time.time() - start_time

        # Parse pytest output for counts
        stdout = res.stdout
        passed_match = re.search(r"(\d+)\s+passed", stdout)
        failed_match = re.search(r"(\d+)\s+failed", stdout)

        passed_count = int(passed_match.group(1)) if passed_match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0
        executed_count = passed_count + failed_count

        verdict = "PASS" if res.returncode == 0 and failed_count == 0 else "FAIL"

        receipt = TargetedTestExecutionReceipt(
            receipt_id=f"test_rec_{hashlib.sha256(f'{wave_id}:{exact_git_head}'.encode('utf-8')).hexdigest()[:12]}",
            wave_id=wave_id,
            exact_git_head=exact_git_head,
            modified_files=modified_files,
            selected_test_files=selected_tests,
            fallback_to_full_suite=is_fallback,
            tests_executed=executed_count,
            tests_passed=passed_count,
            tests_failed=failed_count,
            execution_time_seconds=round(elapsed, 3),
            verdict=verdict,
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt
