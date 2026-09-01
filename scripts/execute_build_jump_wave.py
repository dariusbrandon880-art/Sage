#!/usr/bin/env python3
"""Execute a live 5-flight Big Jump Wave from an explicit mission plan.

F1-F5 are reusable execution slots. This runner deliberately contains no
permanent flight-to-capability mapping; every wave supplies its own mission
assignment in a JSON plan.

Usage:
    python scripts/execute_build_jump_wave.py --mission-plan path/to/plan.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "build_jump_wave_evidence.json"


def load_mission_plan(path: Path) -> tuple[str | None, list[FlightMissionSpec]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Mission plan must be a JSON object")
    wave_id = payload.get("wave_id")
    raw_missions = payload.get("missions")
    if not isinstance(raw_missions, list):
        raise ValueError("Mission plan must contain a 'missions' list")
    missions = [FlightMissionSpec.model_validate(item) for item in raw_missions]
    return wave_id, missions


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute an explicitly assigned 5-flight Big Jump Wave")
    parser.add_argument("--mission-plan", required=True, type=Path, help="JSON file containing the current wave's F1-F5 mission assignments")
    args = parser.parse_args()

    mission_plan = args.mission_plan if args.mission_plan.is_absolute() else repo_root / args.mission_plan
    if not mission_plan.is_file():
        parser.error(f"mission plan not found: {mission_plan}")

    print("=" * 70)
    print("SAGE C2 LIVE BIG JUMP WAVE EXECUTION")
    print("Reusable slots: F1-F5 | Mission assignment: explicit per wave")
    print("=" * 70)

    plan_wave_id, missions = load_mission_plan(mission_plan)
    wave_id = plan_wave_id or f"wave-big-jump-{int(time.time())}"
    engine = BuildJumpWaveEngine(storage_dir=str(repo_root / "evidence_capture"))
    evidence_pkg = engine.execute_wave(wave_id=wave_id, missions=missions)

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence_pkg.model_dump(), indent=2) + "\n", encoding="utf-8")

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
            f"  - [{summary.flight_id}] Mission target: {summary.target} -> Result: {summary.execution_result} "
            f"(Tests Passed: {summary.tests_passed}) SHA: {summary.exact_head[:12]}..."
        )

    if evidence_pkg.reconvergence_verdict != "PASS" or evidence_pkg.successful_flights < 5:
        print("\n[!] BIG JUMP WAVE FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] BIG JUMP WAVE SUCCESSFUL — ALL 5 REUSABLE SLOTS VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
