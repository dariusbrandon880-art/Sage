#!/usr/bin/env python3
"""Execute two Big Jump waves concurrently from an explicit mission plan.

F1-F5 are reusable slots. No permanent slot-to-capability mapping is encoded
here; each wave supplies its own assignments.

Usage:
    python scripts/execute_double_big_jump_wave.py --mission-plan path/to/plan.json
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import subprocess
import sys
import time
from pathlib import Path

from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec
from sage.c2.double_big_jump_contract import (
    DoubleBigJumpWaveSpec,
    reconverge_double_big_jump,
    require_current_head,
    validate_double_big_jump_waves,
)


def get_git_head_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    head = result.stdout.strip()
    if len(head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in head):
        raise RuntimeError(f"Invalid repository HEAD: {head!r}")
    return head


def load_mission_plan(path: Path) -> tuple[DoubleBigJumpWaveSpec, DoubleBigJumpWaveSpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("waves"), list):
        raise ValueError("Double Big Jump mission plan must contain a 'waves' list")
    if len(payload["waves"]) != 2:
        raise ValueError("Double Big Jump mission plan requires exactly two waves")

    waves: list[DoubleBigJumpWaveSpec] = []
    for raw_wave in payload["waves"]:
        if not isinstance(raw_wave, dict):
            raise ValueError("Each wave must be a JSON object")
        wave_id = raw_wave.get("wave_id")
        raw_missions = raw_wave.get("missions")
        if not isinstance(wave_id, str) or not isinstance(raw_missions, list):
            raise ValueError("Each wave requires 'wave_id' and 'missions'")
        missions = tuple(FlightMissionSpec.model_validate(item) for item in raw_missions)
        waves.append(DoubleBigJumpWaveSpec(wave_id=wave_id, missions=missions))

    return validate_double_big_jump_waves(tuple(waves))


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute two explicitly assigned Big Jump Waves")
    parser.add_argument("--mission-plan", required=True, type=Path, help="JSON file containing both waves' F1-F5 assignments")
    args = parser.parse_args()

    mission_plan = args.mission_plan if args.mission_plan.is_absolute() else Path.cwd() / args.mission_plan
    if not mission_plan.is_file():
        parser.error(f"mission plan not found: {mission_plan}")

    waves = load_mission_plan(mission_plan)
    expected_head = get_git_head_sha()
    print("=" * 80)
    print("SAGE C2 — DOUBLE BIG JUMP / DYNAMIC WAVE COMPOSITION")
    print("=" * 80)
    print(f"[*] Anchored repository HEAD: {expected_head}")
    print("[*] Two independent five-slot waves will execute concurrently.")

    engine = BuildJumpWaveEngine()
    results = {}
    start = time.time()

    def run_wave(wave: DoubleBigJumpWaveSpec):
        head = require_current_head(get_git_head_sha(), expected_head)
        return wave.wave_id, engine.execute_wave(wave_id=wave.wave_id, missions=list(wave.missions)), head

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="double-big-jump") as executor:
        futures = [executor.submit(run_wave, wave) for wave in waves]
        for future in as_completed(futures):
            try:
                wave_id, package, head = future.result()
                results[wave_id] = (package, head)
                print(f"[+] {wave_id}: completed at HEAD {head}")
            except Exception as exc:
                print(f"[!] wave execution failed closed: {type(exc).__name__}: {exc}")

    wave_pass = {wave_id: package.reconvergence_verdict.upper() == "PASS" for wave_id, (package, _) in results.items()}
    combined_pass = reconverge_double_big_jump(wave_results=wave_pass, waves=waves) if len(results) == 2 else False
    receipt = {
        "execution": "double_big_jump",
        "anchored_head": expected_head,
        "waves": {
            wave_id: {
                "head": head,
                "reconvergence_verdict": package.reconvergence_verdict,
                "successful_flights": package.successful_flights,
                "total_flights": package.total_flights,
            }
            for wave_id, (package, head) in results.items()
        },
        "elapsed_seconds": round(time.time() - start, 6),
        "combined_verdict": "PASS" if combined_pass else "FAIL_CLOSED",
    }
    output = Path("evidence_capture/double_big_jump_wave_evidence.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[*] Combined verdict: {receipt['combined_verdict']}")
    return 0 if combined_pass else 1


if __name__ == "__main__":
    sys.exit(main())
