#!/usr/bin/env python3
"""Execute a live five-slot Big Jump Wave with explicit per-run missions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import FlightMissionSpec  # noqa: E402
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "multi_frontier_dispatch_evidence.json"


def missions() -> list[FlightMissionSpec]:
    return [
        FlightMissionSpec("F1", "Recon mission", "sage/c2/recon/", "sage/c2/recon/", "evidence_capture/f1_recon.json", "recon"),
        FlightMissionSpec("F2", "Runtime mission", "sage/runtime/", "sage/runtime/", "evidence_capture/f2_runtime.json", "runtime"),
        FlightMissionSpec("F3", "Sports mission", "sage/experimental/sports_quant/", "sage/experimental/sports_quant/", "evidence_capture/f3_sports.json", "sports"),
        FlightMissionSpec("F4", "Verification mission", "tests/c2/verification/", "tests/c2/verification/", "evidence_capture/f4_verification.json", "verification"),
        FlightMissionSpec("F5", "Warehouse mission", "evidence_capture/warehouse/", "evidence_capture/warehouse/", "evidence_capture/f5_warehouse.json", "warehouse"),
    ]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE MULTI-FRONTIER CAPABILITY DISPATCH")
    print("=" * 70)

    dispatcher = MultiFrontierDispatcher()
    receipt = dispatcher.dispatch_all(missions())

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    print(f"Commit SHA: {receipt.commit_sha}")
    print(f"Total Slots: {receipt.summary.get('total_flights')}")
    print(f"Collision Count: {receipt.collision_count}")
    print(f"Wave Verdict: {receipt.wave_verdict}")
    print(f"Evidence Captured: {EVIDENCE_PATH}")

    for fr in receipt.flight_receipts:
        print(f"  - [{fr.flight_id}] ({fr.frontier_name}) -> {fr.status} [{fr.proof_type}] SHA: {fr.receipt_hash[:12]}...")

    if receipt.wave_verdict != "PASS" or receipt.collision_count > 0:
        print("\n[!] MULTI-FRONTIER DISPATCH FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] MULTI-FRONTIER DISPATCH SUCCESSFUL — 5 REUSABLE SLOTS VERIFIED WITH 0 COLLISIONS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
