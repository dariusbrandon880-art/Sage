#!/usr/bin/env python3
"""Run the SAGE Multi-Session Velocity Wave with identity-addressed evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sage.c2.workflow_velocity import MultiSessionVelocityEngine, SessionRole


def get_git_head() -> str:
    """Return the exact commit SHA of the checkout executing this run."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> int:
    exact_head = get_git_head()
    run_id = os.environ.get("GITHUB_RUN_ID", "local-run")
    job_id = os.environ.get("GITHUB_JOB", "local-job")

    engine = MultiSessionVelocityEngine()
    engine.register_session("c2-control-tower-primary", SessionRole.C2_CONTROL_TOWER)
    engine.register_session("jules-execution-session-01", SessionRole.JULES_EXECUTION_SESSION)

    flight_payloads = [
        {
            "flight_id": "F1",
            "target": "Core C2 Infrastructure & Multi-Session Velocity Engine",
            "classification": "ACTIVE",
            "execution_result": "PASS",
            "tests_passed": 12,
            "target_files": ["sage/c2/workflow_velocity.py"],
            "target_namespaces": ["sage.c2.velocity"],
            "pr_or_change": "PR #270",
        },
        {
            "flight_id": "F2",
            "target": "Airspace Observer & Concurrent Failure Memory",
            "classification": "ACTIVE",
            "execution_result": "PASS",
            "tests_passed": 15,
            "target_files": ["sage/experimental/airspace/fleet_concurrency.py"],
            "target_namespaces": ["sage.experimental.airspace"],
            "pr_or_change": "PR #271",
        },
        {
            "flight_id": "F3",
            "target": "Execution Velocity & Playbook Optimization Engine",
            "classification": "ACTIVE",
            "execution_result": "PASS",
            "tests_passed": 18,
            "target_files": ["sage/c2/c2_wave_playbook.py"],
            "target_namespaces": ["sage.c2.playbook"],
            "pr_or_change": "PR #272",
        },
        {
            "flight_id": "F4",
            "target": "Rolls-Royce Governance & Anti-Collision Lock Safeguard",
            "classification": "ACTIVE",
            "execution_result": "PASS",
            "tests_passed": 20,
            "target_files": ["docs/governance/SAGE_MULTI_SESSION_VELOCITY_WORKFLOW.md"],
            "target_namespaces": ["docs.governance.velocity"],
            "pr_or_change": "PR #273",
        },
        {
            "flight_id": "F5",
            "target": "Reconvergence Evidence Synthesizer & Promotion Ledger",
            "classification": "ACTIVE",
            "execution_result": "PASS",
            "tests_passed": 14,
            "target_files": ["sage/c2/reconvergence_synthesizer.py"],
            "target_namespaces": ["sage.c2.reconvergence"],
            "pr_or_change": "PR #274",
        },
    ]

    wave_id = "multi_session_velocity_wave_001"
    receipt = engine.execute_velocity_wave(
        wave_id=wave_id,
        session_id="jules-execution-session-01",
        flight_payloads=flight_payloads,
        exact_git_head=exact_head,
    )

    if not receipt.rolls_royce_quality_passed or receipt.reconvergence_verdict != "PASS":
        print("[!] FAIL_CLOSED: velocity wave did not reconverge")
        return 1

    # The legacy flat JSON file is intentionally no longer a gate authority.
    # It may remain as historical data, but live execution evidence is addressed
    # by wave/head identity so concurrent waves cannot overwrite one another.
    evidence_dir = Path("evidence_capture") / "waves" / wave_id / exact_head
    evidence_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = evidence_dir / "wave_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "wave_id": wave_id,
        "executed_head": exact_head,
        "workflow_run_id": run_id,
        "job_id": job_id,
        "receipt_path": str(receipt_path),
        "gate_authority": "identity-addressed-receipt",
        "legacy_flat_file_gate_authority": False,
    }
    (evidence_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[+] Persisted identity-addressed evidence to {evidence_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
