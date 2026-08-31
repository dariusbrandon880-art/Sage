#!/usr/bin/env python3
"""Execute Wave A — Execution Intelligence Big Jump Wave.

F1-F5 are reusable execution slots. Current-wave mission identity is carried
by the target assignment and never encoded into the slot id.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from sage.c2.execution_intelligence import WorkflowVelocityController
from sage.c2.reusable_flight_slots import SAGE_FLIGHT_SLOTS


def get_git_head_sha() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    sha = res.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise ValueError(f"Invalid exact git HEAD commit SHA: {sha}")
    return sha


def main():
    head_sha = get_git_head_sha()
    print("[*] Starting Wave A (Execution Intelligence) Execution...")
    print(f"    - Exact git HEAD SHA: {head_sha}")

    flights = [
        {"flight_id": "F1", "target": "Workflow Velocity Controller"},
        {"flight_id": "F2", "target": "Adaptive Concurrency Governor"},
        {"flight_id": "F3", "target": "Admission & Throttling System"},
        {"flight_id": "F4", "target": "Cryptographic Concurrency Evidence"},
        {"flight_id": "F5", "target": "Execution Intelligence Reconvergence"},
    ]
    if tuple(flight["flight_id"] for flight in flights) != SAGE_FLIGHT_SLOTS:
        raise RuntimeError("Wave A flight plan drifted from the canonical reusable slot set")

    controller = WorkflowVelocityController()
    receipt = controller.execute_execution_intelligence_wave(
        wave_id="wave_execution_intelligence_v1",
        exact_git_head=head_sha,
        flights=flights,
        requested_workers=4,
    )

    output_path = Path("evidence_capture/execution_intelligence_wave_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt.model_dump(), indent=2), encoding="utf-8")

    print("[+] Wave A Completed Cleanly!")
    print(f"    - Receipt ID: {receipt.receipt_id}")
    print(f"    - Concurrent Workers Used: {receipt.concurrent_workers_used}")
    print(f"    - Rolls-Royce Passed: {receipt.rolls_royce_quality_passed}")
    print(f"    - Evidence saved to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
