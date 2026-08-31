#!/usr/bin/env python3
"""Execute a live 5-slot Big Jump Wave under SAGE C2 governance.

The five flight IDs are reusable slots. This runner supplies the missions for
this invocation; no slot owns a permanent capability.
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


def current_wave_missions() -> list[FlightMissionSpec]:
    """Return five independent missions for this invocation.

    These assignments are intentionally per-run data, not permanent F1-F5
    capability ownership. C2 may replace any mission with any other authorized
    target without changing the flight-slot model.
    """
    return [
        FlightMissionSpec("F1", "Repository recon", "sage/c2/", "sage/c2/", "evidence_capture/f1.json", "current-repo-recon"),
        FlightMissionSpec("F2", "Runtime repair", "sage/runtime/", "sage/runtime/", "evidence_capture/f2.json", "runtime-repair"),
        FlightMissionSpec("F3", "Sports analysis", "sage/experimental/sports_quant/", "sage/experimental/sports_quant/", "evidence_capture/f3.json", "sports-analysis"),
        FlightMissionSpec("F4", "Governance verification", "tests/c2/", "tests/c2/", "evidence_capture/f4.json", "governance-verification"),
        FlightMissionSpec("F5", "Evidence reconciliation", "evidence_capture/", "evidence_capture/", "evidence_capture/f5.json", "evidence-reconciliation"),
    ]


def main() -> int:
    print("=" * 70)
    print("SAGE C2 LIVE BIG JUMP WAVE EXECUTION")
    print("=" * 70)

    wave_id = f"wave-big-jump-{int(time.time())}"
    engine = BuildJumpWaveEngine(storage_dir=str(repo_root / "evidence_capture"))
    evidence_pkg = engine.execute_wave(wave_id=wave_id, missions=current_wave_missions())

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence_pkg.model_dump(), f, indent=2)

    print(f"Wave ID: {evidence_pkg.wave_id}")
    print(f"Total Slots: {evidence_pkg.total_flights}")
    print(f"Successful Slots: {evidence_pkg.successful_flights}")
    print(f"20-Cell Advancement Matrix Cell Count: {len(evidence_pkg.advancement_matrix_20_cells)}")
    print(f"First Pass Verification Rate: {evidence_pkg.first_pass_verification_rate}%")
    print(f"Reconvergence Verdict: {evidence_pkg.reconvergence_verdict}")
    print(f"Package Hash: {evidence_pkg.package_hash}")
    print(f"Evidence Persisted: {EVIDENCE_PATH}")

    for summary in evidence_pkg.flight_summaries:
        print(
            f"  - [{summary.flight_id}] Mission: {summary.pr_or_change} -> Result: {summary.execution_result} "
            f"(Tests Passed: {summary.tests_passed}) SHA: {summary.exact_head[:12]}..."
        )

    if evidence_pkg.reconvergence_verdict != "PASS" or evidence_pkg.successful_flights < 5:
        print("\n[!] BIG JUMP WAVE FAILED OR HELD", file=sys.stderr)
        return 1

    print("\n[✓] BIG JUMP WAVE SUCCESSFUL — ALL 5 REUSABLE SLOTS VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
