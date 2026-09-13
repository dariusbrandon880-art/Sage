#!/usr/bin/env python3
"""Execute live multi-frontier capability dispatch across 5 isolated flight vectors.

Outputs observable evidence to evidence_capture/multi_frontier_dispatch_evidence.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path reliably
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import FlightMissionSpec  # noqa: E402
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "multi_frontier_dispatch_evidence.json"

DEFAULT_MISSIONS = [
    FlightMissionSpec(
        flight_id="F1",
        frontier_name="Multi-Frontier Dispatcher",
        target_path="sage/c2/multi_frontier_dispatch.py",
        collision_zone="sage.c2.multi_frontier_dispatch",
        evidence_ref="evidence_capture/multi_frontier_dispatch_evidence.json",
        pr_or_change="adaptive-parallel-frontier-convergence",
        test_references=["tests/c2/test_multi_frontier_dispatch.py"],
    ),
    FlightMissionSpec(
        flight_id="F2",
        frontier_name="Frontier Intelligence Bridge",
        target_path="sage/c2/frontier_intelligence_bridge.py",
        collision_zone="sage.c2.frontier_intelligence_bridge",
        evidence_ref="evidence_capture/frontier_intelligence_bridge_evidence.json",
        pr_or_change="adaptive-parallel-frontier-convergence",
        test_references=["tests/test_frontier_intelligence_bridge.py"],
    ),
    FlightMissionSpec(
        flight_id="F3",
        frontier_name="Parallel Frontier Supervisor",
        target_path="sage/experimental/parallel_frontier_supervisor.py",
        collision_zone="sage.experimental.parallel_frontier_supervisor",
        evidence_ref="evidence_capture/parallel_frontier_supervisor_evidence.json",
        pr_or_change="adaptive-parallel-frontier-convergence",
        test_references=["tests/experimental/test_parallel_frontier_supervisor.py"],
    ),
    FlightMissionSpec(
        flight_id="F4",
        frontier_name="Coherent Frontier Engine",
        target_path="sage/experimental/coherent_frontier.py",
        collision_zone="sage.experimental.coherent_frontier",
        evidence_ref="evidence_capture/coherent_frontier_evidence.json",
        pr_or_change="adaptive-parallel-frontier-convergence",
        test_references=["tests/experimental/test_coherent_frontier.py"],
    ),
    FlightMissionSpec(
        flight_id="F5",
        frontier_name="Frontier Tree Engine",
        target_path="sage/experimental/frontier_tree.py",
        collision_zone="sage.experimental.frontier_tree",
        evidence_ref="evidence_capture/frontier_tree_evidence.json",
        pr_or_change="adaptive-parallel-frontier-convergence",
        test_references=["tests/experimental/test_frontier_tree.py"],
    ),
]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE MULTI-FRONTIER CAPABILITY DISPATCH")
    print("=" * 70)

    dispatcher = MultiFrontierDispatcher()
    receipt = dispatcher.dispatch_all(missions=DEFAULT_MISSIONS)

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
            f"  - [{fr.flight_id}] ({fr.frontier_name}) -> {fr.status} [{fr.proof_type}] SHA: {fr.receipt_hash[:12]}..."
        )

    if receipt.wave_verdict != "PASS" or receipt.collision_count > 0:
        print("\n[!] MULTI-FRONTIER DISPATCH FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] MULTI-FRONTIER DISPATCH SUCCESSFUL — 5 MISSIONS VERIFIED WITH 0 COLLISIONS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
