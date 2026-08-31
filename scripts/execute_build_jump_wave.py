#!/usr/bin/env python3
"""Execute a live five-flight Big Jump Wave with explicitly assigned missions.

The five flight IDs are reusable execution slots. This runner supplies one
selected mission set for this invocation; it does not define permanent flight
roles.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "build_jump_wave_evidence.json"


def selected_missions() -> list[FlightMissionSpec]:
    """Return one wave-specific mission assignment for the reusable five slots."""
    assignments = (
        ("F1", "runtime-repair", "sage/runtime/engine.py", "sage/runtime/", "evidence_capture/f1_runtime_repair.json", "runtime repair", ["tests/test_system_frame.py"]),
        ("F2", "transport-hardening", "sage/runtime/interface_transport.py", "sage/runtime/", "evidence_capture/f2_transport_hardening.json", "transport hardening", ["tests/runtime/test_interface_transport.py"]),
        ("F3", "governance-attack", "sage/runtime/model_gateway.py", "sage/runtime/", "evidence_capture/f3_governance_attack.json", "governance attack", ["tests/runtime/test_protocol_governance.py"]),
        ("F4", "c2-antidrift", "sage/c2/chatgpt_c2_contract.py", "sage/c2/contract/", "evidence_capture/f4_antidrift.json", "C2 anti-drift repair", ["tests/c2/test_chatgpt_c2_exact_order_anti_drift.py"]),
        ("F5", "convergence-test", "sage/c2/reconvergence_synthesizer.py", "sage/c2/reconvergence/", "evidence_capture/f5_convergence_test.json", "reconvergence test", ["tests/c2/test_reconvergence_synthesizer.py"]),
    )
    return [
        FlightMissionSpec(
            flight_id=flight_id,
            mission_name=mission_name,
            target_path=target_path,
            collision_zone=collision_zone,
            evidence_ref=evidence_ref,
            pr_or_change=pr_or_change,
            test_references=test_references,
        )
        for flight_id, mission_name, target_path, collision_zone, evidence_ref, pr_or_change, test_references in assignments
    ]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE BIG JUMP WAVE EXECUTION")
    print("=" * 70)

    wave_id = f"wave-big-jump-{int(time.time())}"
    engine = BuildJumpWaveEngine(storage_dir=str(repo_root / "evidence_capture"))
    evidence_pkg = engine.execute_wave(wave_id=wave_id, missions=selected_missions())

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

    print("\n[✓] BIG JUMP WAVE SUCCESSFUL — ALL 5 ASSIGNED FLIGHTS VERIFIED (20/20 ADVANCEMENT CELLS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
