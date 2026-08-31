#!/usr/bin/env python3
"""Execute two canonical Big Jump waves concurrently.

Double Big Jump is composition: each wave uses the same canonical Big Jump
engine with reusable F1..F5 slots and an explicit mission plan. No permanent
flight roles and no historical HEAD fallback are permitted.
"""

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
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    head = result.stdout.strip()
    if len(head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in head):
        raise RuntimeError(f"Invalid repository HEAD: {head!r}")
    return head


def build_wave(wave_id: str, prefix: str) -> DoubleBigJumpWaveSpec:
    targets = (
        ("execution_intelligence.py", "tests/c2/test_execution_intelligence_wave.py"),
        ("governance_intelligence.py", "tests/c2/test_governance_intelligence_wave.py"),
        ("build_jump_wave.py", "tests/c2/test_build_jump_wave.py"),
        ("multi_frontier_dispatch.py", "tests/c2/test_multi_frontier_dispatch.py"),
        ("double_big_jump_contract.py", "tests/c2/test_double_big_jump_contract.py"),
    )
    missions = tuple(
        FlightMissionSpec(
            flight_id=f"F{i}",
            frontier_name=f"{prefix}-{i}-{Path(target).stem}",
            target_path=f"sage/c2/{target}",
            collision_zone=f"sage.c2.{Path(target).stem}",
            evidence_ref=f"evidence_capture/waves/{wave_id}/F{i}_receipt.json",
            pr_or_change=f"Double Big Jump {wave_id} mission F{i}",
            test_references=[test_path],
        )
        for i, (target, test_path) in enumerate(targets, start=1)
    )
    return DoubleBigJumpWaveSpec(wave_id=wave_id, missions=missions)


def main() -> int:
    expected_head = get_git_head_sha()
    wave_a = build_wave("double-wave-A", "A")
    wave_b = build_wave("double-wave-B", "B")
    waves = validate_double_big_jump_waves((wave_a, wave_b))

    print("=" * 80)
    print("SAGE C2 — DOUBLE BIG JUMP / CANONICAL WAVE COMPOSITION")
    print("=" * 80)
    print(f"[*] Anchored repository HEAD: {expected_head}")
    print("[*] Two canonical five-slot waves will execute concurrently.")

    engine = BuildJumpWaveEngine()
    results = {}
    start = time.time()

    def run_wave(wave: DoubleBigJumpWaveSpec):
        actual_head = get_git_head_sha()
        head = require_current_head(actual_head, expected_head)
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

    wave_pass = {
        wave_id: bool(package.reconvergence_passed)
        for wave_id, (package, _) in results.items()
    }
    combined_pass = reconverge_double_big_jump(
        wave_results=wave_pass,
        waves=waves,
    ) if len(results) == 2 else False

    receipt = {
        "execution": "double_big_jump",
        "anchored_head": expected_head,
        "waves": {
            wave_id: {
                "head": head,
                "reconvergence_passed": wave_pass.get(wave_id, False),
            }
            for wave_id, (_, head) in results.items()
        },
        "elapsed_seconds": round(time.time() - start, 6),
        "combined_verdict": "PASS" if combined_pass else "FAIL_CLOSED",
    }
    output = Path("evidence_capture/double_big_jump_wave_evidence.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[*] Combined verdict: {receipt['combined_verdict']}")
    print(f"[*] Evidence: {output}")
    return 0 if combined_pass else 1


if __name__ == "__main__":
    sys.exit(main())
