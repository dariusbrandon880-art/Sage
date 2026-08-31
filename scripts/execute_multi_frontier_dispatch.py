#!/usr/bin/env python3
"""Execute live multi-frontier capability dispatch across five reusable flight slots.

The selected mission set is wave-specific; F1-F5 have no permanent frontier roles.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher  # noqa: E402
from execute_build_jump_wave import selected_missions  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "multi_frontier_dispatch_evidence.json"


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE MULTI-FRONTIER CAPABILITY DISPATCH")
    print("=" * 70)

    missions = selected_missions()
    dispatcher = MultiFrontierDispatcher()
    receipt = dispatcher.dispatch_all(missions)

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    print(f"Commit SHA: {receipt.commit_sha}")
    print(f"Total Flights: {receipt.summary.get('total_flights')}")
    print(f"Collision Count: {receipt.collision_count}")
    print(f"Wave Verdict: {receipt.wave_verdict}")
    print(f"Evidence Captured: {EVIDENCE_PATH}")

    for fr in receipt.flight_receipts:
        print(
            f"  - [{fr.flight_id}] ({fr.mission_name}) -> {fr.status} "
            f"[{fr.proof_type}] SHA: {fr.receipt_hash[:12]}..."
        )

    if receipt.wave_verdict != "PASS" or receipt.collision_count > 0:
        print("\n[!] MULTI-FRONTIER DISPATCH FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] MULTI-FRONTIER DISPATCH SUCCESSFUL — 5 CURRENT MISSIONS VERIFIED WITH 0 COLLISIONS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
