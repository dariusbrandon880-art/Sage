#!/usr/bin/env python3
"""Execute a live 5-flight Big Jump Wave under SAGE C2 governance.

The mission plan is supplied by the current wave through
``SAGE_WAVE_MISSIONS_JSON``.  No permanent F1-F5 mission table is embedded in
this executor.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "build_jump_wave_evidence.json"


def _load_missions() -> list[FlightMissionSpec]:
    raw = os.environ.get("SAGE_WAVE_MISSIONS_JSON")
    if not raw:
        raise ValueError("SAGE_WAVE_MISSIONS_JSON is required; F1-F5 have no permanent mission assignment")
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("SAGE_WAVE_MISSIONS_JSON must be a JSON list of five mission assignments")
    return [FlightMissionSpec.model_validate(item) for item in payload]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE BIG JUMP WAVE EXECUTION")
    print("=" * 70)

    try:
        missions = _load_missions()
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"[!] WAVE MISSION PLAN REJECTED: {exc}", file=sys.stderr)
        return 2

    wave_id = f"wave-big-jump-{int(time.time())}"
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
