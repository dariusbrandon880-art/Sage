#!/usr/bin/env python3
"""Execute the Execution Intelligence capability as an explicit mission set.

F1-F5 are reusable slots; capability names are mission targets, never slot identities.
"""

import json
import subprocess
import sys
from pathlib import Path

from sage.c2.execution_intelligence import WorkflowVelocityController


def get_git_head_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    head = result.stdout.strip()
    if len(head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in head):
        raise RuntimeError(f"Invalid repository HEAD: {head!r}")
    return head


def main():
    head_sha = get_git_head_sha()
    print("[*] Starting Execution Intelligence mission set")
    print(f"    - Exact git HEAD SHA: {head_sha}")

    flights = [
        {"flight_id": "F1", "mission": "Workflow Velocity Controller"},
        {"flight_id": "F2", "mission": "Adaptive Concurrency Governor"},
        {"flight_id": "F3", "mission": "Admission and Throttling System"},
        {"flight_id": "F4", "mission": "Cryptographic Concurrency Evidence"},
        {"flight_id": "F5", "mission": "Execution Intelligence Reconvergence"},
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
    output_path.write_text(json.dumps(receipt.model_dump(), indent=2) + "\n", encoding="utf-8")

    print(f"[+] Receipt ID: {receipt.receipt_id}")
    print(f"    - Concurrent Workers Used: {receipt.concurrent_workers_used}")
    print(f"    - Rolls-Royce Passed: {receipt.rolls_royce_quality_passed}")
    return 0 if receipt.rolls_royce_quality_passed else 1


if __name__ == "__main__":
    sys.exit(main())
