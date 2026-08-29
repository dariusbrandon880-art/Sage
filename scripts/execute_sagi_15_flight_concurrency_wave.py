#!/usr/bin/env python3
"""Execute the SAGI 15-Flight Concurrency Wave with identity-addressed evidence."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sage.experimental.sagi_15_flight_concurrency import SAGI15FlightConcurrencyEngine


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

    engine = SAGI15FlightConcurrencyEngine()
    wave_id = "sagi_15_flight_concurrency_wave_001"

    print(f"=== SAGE SAGI 15-Flight Concurrency Wave Execution Starting ===")
    print(f"[+] Active Git HEAD SHA: {exact_head}")

    receipt = engine.execute_concurrency_wave(
        wave_id=wave_id,
        exact_git_head=exact_head,
    )

    if not receipt.rolls_royce_quality_passed or receipt.reconvergence_verdict != "PASS":
        print("[!] FAIL_CLOSED: 15-flight concurrency wave did not reconverge")
        return 1

    print(f"[+] Concurrency Wave Reconverged: VERDICT={receipt.reconvergence_verdict}")
    print(f"[+] Active Execution Sessions: {receipt.active_sessions}")
    print(f"[+] Total Flights Executed: {receipt.total_flights}/{receipt.successful_flights}")
    print(f"[+] Total Lifecycle Cells Advanced: {receipt.total_advancement_cells}/60")
    print(f"[+] Cryptographic Receipt Hash: {receipt.receipt_hash}")

    # Persist flat historical file
    flat_path = Path("evidence_capture/sagi_15_flight_concurrency_evidence.json")
    flat_data = receipt.model_dump()
    flat_path.write_text(json.dumps(flat_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Persist identity-addressed evidence directory
    evidence_dir = Path("evidence_capture") / "waves" / wave_id / exact_head
    evidence_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = evidence_dir / "wave_receipt.json"
    receipt_path.write_text(json.dumps(flat_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "wave_id": wave_id,
        "executed_head": exact_head,
        "workflow_run_id": run_id,
        "job_id": job_id,
        "receipt_path": str(receipt_path),
        "total_flights": 15,
        "total_cells": 60,
        "gate_authority": "identity-addressed-receipt",
    }
    (evidence_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"[+] Persisted evidence to {flat_path} and {evidence_dir}")
    print("=== SAGE SAGI 15-Flight Concurrency Wave Execution Completed Successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
