#!/usr/bin/env python3
"""Runner script to execute the canonical SAGE Whole-Organism Loop and persist evidence receipt."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from sage.c2.whole_organism_loop import WholeOrganismLoopEngine


def run_pytest_executor(test_file: str) -> dict[str, object]:
    """Execute real pytest suite for a flight target and extract genuine pass counts."""
    res = subprocess.run([sys.executable, "-m", "pytest", test_file], capture_output=True, text=True)
    tests_passed = 0
    if res.returncode == 0:
        match = re.search(r"(\d+)\s+passed", res.stdout)
        if match:
            tests_passed = int(match.group(1))
        return {"execution_result": "PASS", "tests_passed": tests_passed}
    return {"execution_result": "FAIL", "tests_passed": 0, "blocker": res.stderr or res.stdout}


def main() -> int:
    print("[SAGE::C2::ORGANISM] Starting Canonical Whole-Organism End-to-End Loop Execution...")

    engine = WholeOrganismLoopEngine()
    head_sha = engine.get_current_head_sha()
    print(f"    - Exact Git HEAD SHA: {head_sha}")

    mission_id = "mission_whole_organism_convergence_2026"
    session_id = "jules_organism_session_001"

    flight_payloads = [
        {
            "flight_id": "F1",
            "target": "SAGI Cognition Nexus & Capability Graph Discovery",
            "classification": "ACTIVE",
            "target_files": ["sage/c2/capability_graph.py"],
            "target_namespaces": ["sage.c2.capability_graph"],
            "pr_or_change": "PR #380",
            "executor": lambda: run_pytest_executor("tests/c2/test_capability_graph.py"),
        },
        {
            "flight_id": "F2",
            "target": "Master Archive & Governance Intelligence Bridge",
            "classification": "ACTIVE",
            "target_files": ["sage/c2/governance_intelligence.py"],
            "target_namespaces": ["sage.c2.governance"],
            "pr_or_change": "PR #381",
            "executor": lambda: run_pytest_executor("tests/c2/test_governance_intelligence_wave.py"),
        },
        {
            "flight_id": "F3",
            "target": "C2 Executive Mission Control & Reconvergence Synthesizer",
            "classification": "ACTIVE",
            "target_files": ["sage/c2/reconvergence_synthesizer.py"],
            "target_namespaces": ["sage.c2.reconvergence"],
            "pr_or_change": "PR #382",
            "executor": lambda: run_pytest_executor("tests/c2/test_reconvergence_synthesizer.py"),
        },
        {
            "flight_id": "F4",
            "target": "Validation Engine & Whole-Organism Jigsaw Verification",
            "classification": "ACTIVE",
            "target_files": ["sage/c2/organism_jigsaw.py"],
            "target_namespaces": ["sage.c2.organism_jigsaw"],
            "pr_or_change": "PR #383",
            "executor": lambda: run_pytest_executor("tests/c2/test_organism_jigsaw.py"),
        },
        {
            "flight_id": "F5",
            "target": "Five Flights Execution, Learning Feedback & Immersion Projection",
            "classification": "ACTIVE",
            "target_files": ["sage/c2/whole_organism_loop.py"],
            "target_namespaces": ["sage.c2.whole_organism_loop"],
            "pr_or_change": "PR #384",
            "executor": lambda: run_pytest_executor("tests/c2/test_whole_organism_loop.py"),
        },
    ]

    receipt = engine.execute_whole_organism_loop(
        mission_id=mission_id,
        session_id=session_id,
        flight_payloads=flight_payloads,
        exact_git_head=head_sha,
    )

    if not receipt.verify():
        print("ERROR: Whole-Organism receipt verification failed!", file=sys.stderr)
        return 1

    print(f"[+] SUCCESS: Whole-Organism Loop Executed and Verified!")
    print(f"    - Mission ID: {receipt.mission_id}")
    print(f"    - Exact HEAD: {receipt.exact_git_head}")
    print(f"    - Jigsaw Gates Passed: {receipt.jigsaw_gates_passed}/{receipt.jigsaw_total_gates}")
    print(f"    - Outcome Quality Score: {receipt.outcome_quality_score:.4f}")
    print(f"    - Growth Verdict: {receipt.growth_verdict}")
    print(f"    - Next Frontier: {receipt.next_frontier}")
    print(f"    - Receipt Hash: {receipt.receipt_hash}")
    print(f"    - Evidence saved to evidence_capture/whole_organism_flight_receipt.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
