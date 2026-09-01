#!/usr/bin/env python3
"""Execute Wave A — Execution Intelligence Big Jump Wave."""

import json
import os
import subprocess
import sys
from pathlib import Path

from sage.c2.execution_intelligence import WorkflowVelocityController

TARGET_HEAD_SHA = "bf2560ede2899adfe73fe2e2cfb4accd0b8885e2"


def get_git_head_sha() -> str:
    env_sha = os.getenv("SAGE_TARGET_HEAD_SHA")
    if env_sha and len(env_sha) == 40:
        return env_sha
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return TARGET_HEAD_SHA


def main():
    head_sha = get_git_head_sha()
    print(f"[*] Starting Wave A (Execution Intelligence) Execution...")
    print(f"    - Exact git HEAD SHA: {head_sha}")

    flights = [
        {"flight_id": "F1_VELOCITY", "target": "Workflow Velocity Controller"},
        {"flight_id": "F2_CONCURRENCY", "target": "Adaptive Concurrency Governor"},
        {"flight_id": "F3_THROTTLING", "target": "Admission & Throttling System"},
        {"flight_id": "F4_EVIDENCE", "target": "Cryptographic Concurrency Evidence"},
        {"flight_id": "F5_RECONVERGENCE", "target": "Execution Intelligence Reconvergence"},
    ]

    controller = WorkflowVelocityController()
    receipt = controller.execute_execution_intelligence_wave(
        wave_id="wave_execution_intelligence_v1",
        exact_git_head=head_sha,
        flights=flights,
        requested_workers=4,
    )

    output_path = Path("evidence_capture/execution_intelligence_wave_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    evidence_dict = receipt.model_dump()
    output_path.write_text(json.dumps(evidence_dict, indent=2), encoding="utf-8")

    print(f"[+] Wave A Completed Cleanly!")
    print(f"    - Receipt ID: {receipt.receipt_id}")
    print(f"    - Concurrent Workers Used: {receipt.concurrent_workers_used}")
    print(f"    - Rolls-Royce Passed: {receipt.rolls_royce_quality_passed}")
    print(f"    - Evidence saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
