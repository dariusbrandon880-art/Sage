#!/usr/bin/env python3
"""Execute live 5-flight Big Jump Wave under SAGE C2 governance.

Outputs evidence package to evidence_capture/build_jump_wave_evidence.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "build_jump_wave_evidence.json"


def build_canonical_wave_missions(wave_id: str) -> list[FlightMissionSpec]:
    targets = (
        ("execution_intelligence.py", "tests/c2/test_execution_intelligence_wave.py"),
        ("governance_intelligence.py", "tests/c2/test_governance_intelligence_wave.py"),
        ("build_jump_wave.py", "tests/c2/test_build_jump_wave.py"),
        ("multi_frontier_dispatch.py", "tests/c2/test_multi_frontier_dispatch.py"),
        ("double_big_jump_contract.py", "tests/c2/test_double_big_jump_contract.py"),
    )
    return [
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name=f"canonical-wave-F{i}-{Path(target).stem}",
            target_path=f"sage/c2/{target}",
            collision_zone=f"sage.c2.{Path(target).stem}",
            evidence_ref=f"evidence_capture/waves/{wave_id}/F{i}_receipt.json",
            pr_or_change=f"Canonical Big Jump Wave mission F{i}",
            test_references=[test_path],
        )
        for i, (target, test_path) in enumerate(targets, start=1)
    ]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE BIG JUMP WAVE EXECUTION")
    print("=" * 70)

    wave_id = f"wave-big-jump-{int(time.time())}"
    missions = build_canonical_wave_missions(wave_id)
    engine = BuildJumpWaveEngine(storage_dir=str(repo_root / "evidence_capture"))
    evidence_pkg = engine.execute_wave(wave_id=wave_id, missions=missions)

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence_pkg.model_dump(), f, indent=2)

    print(f"Wave ID: {evidence_pkg.wave_id}")
    print(f"Total Flights: {evidence_pkg.total_flights}")
    print(f"Successful Flights: {evidence_pkg.successful_flights}")
    print(f"20-Cell Advancement Matrix Cell Count: {len(evidence_pkg.advancement_matrix_20_cells)}")
    print(f"First Pass Verification Rate: {evidence_pkg.first_pass_verification_rate}%")
    print(f"Reconvergence Verdict: {evidence_pkg.reconvergence_verdict}")
    print(f"Package Hash: {evidence_pkg.package_hash}")
    print(f"Evidence Persisted: {EVIDENCE_PATH}")

    for summary in evidence_pkg.flight_summaries:
        print(
            f"  - [{summary.flight_id}] Target: {summary.target} -> Result: {summary.execution_result} "
            f"(Tests Passed: {summary.tests_passed}) SHA: {summary.exact_head[:12]}..."
        )

    if evidence_pkg.reconvergence_verdict != "PASS" or evidence_pkg.successful_flights < 5:
        print("\n[!] BIG JUMP WAVE FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] BIG JUMP WAVE SUCCESSFUL — ALL 5 FLIGHTS VERIFIED (20/20 ADVANCEMENT CELLS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
