#!/usr/bin/env python3
"""Runner script to execute the authorized 5-flight SAGE C2 Build Jump Wave.

Dispatches Flight 1 to Flight 5 and persists individual receipts and wave reconvergence evidence
to evidence_capture/build_jump_wave_evidence.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sage.c2.build_jump_wave import BuildJumpWaveEngine


def main() -> None:
    print("================================================================================")
    print("SAGE C2 — BUILD JUMP WAVE EXECUTION")
    print("================================================================================")

    engine = BuildJumpWaveEngine()
    print(f"Commit SHA: {engine.commit_sha}\n")

    print("Dispatching 5 Build Jump Wave flights...")
    wave_receipt = engine.dispatch_wave()

    for flight in wave_receipt.flight_receipts:
        print(f"[{flight.flight_id}] ({flight.frontier_lane}): {flight.status}")
        print(f"  Mission: {flight.mission_id}")
        print(f"  Receipt Type: {flight.receipt_type}")
        print(f"  Boundary Scope: {flight.boundary_scope}")
        print(f"  Receipt SHA-256: {flight.receipt_hash}\n")

    print(f"Collisions Detected: {wave_receipt.collision_count}")
    print(f"Wave Verdict: {wave_receipt.wave_verdict}")

    evidence_dir = REPO_ROOT / "evidence_capture"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "build_jump_wave_evidence.json"

    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(wave_receipt.to_dict(), f, indent=2)

    print(f"\nPersisted Build Jump Wave evidence to {evidence_file}")
    print("================================================================================")

    if wave_receipt.wave_verdict != "PASS":
        print("BUILD JUMP WAVE FAILED OR REJECTED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
