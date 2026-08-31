#!/usr/bin/env python3
"""Execute Double Big Jump Wave with fail-closed concurrency proof.

Wave A and Wave B are independent mission waves. Their execution must overlap
at a synchronization barrier, and both receipts must bind to the same exact
observed repository HEAD. Historical fallback SHAs are forbidden.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Barrier
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Mapping

from scripts.execute_execution_intelligence_wave import main as run_wave_a
from scripts.execute_governance_intelligence_wave import main as run_wave_b


def get_git_head_sha() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    sha = res.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise ValueError(f"Invalid exact git HEAD commit SHA: {sha}")
    return sha


def execute_parallel_waves(
    wave_a: Callable[[], int],
    wave_b: Callable[[], int],
    barrier: Barrier,
) -> Mapping[str, int]:
    """Run both waves concurrently and require both to cross the start barrier."""

    def gated(wave: Callable[[], int]) -> int:
        barrier.wait(timeout=30)
        return wave()

    results: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="double-big-jump") as executor:
        futures = {
            executor.submit(gated, wave_a): "WAVE_A",
            executor.submit(gated, wave_b): "WAVE_B",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = int(future.result())
            except Exception as exc:
                print(f"[!] {name} execution encountered error: {exc}")
                results[name] = 1
    return results


def reconcile_receipts(rec_a: Mapping[str, object], rec_b: Mapping[str, object], head_sha: str) -> bool:
    """Require both receipts to prove the same exact HEAD and successful verdicts."""

    if rec_a.get("exact_git_head") != head_sha or rec_b.get("exact_git_head") != head_sha:
        print("[!] FAIL_CLOSED: one or both wave receipts are bound to a stale or mismatched SHA")
        return False
    verdict_a = rec_a.get("rolls_royce_quality_passed") is True
    verdict_b = rec_b.get("fail_closed_verdict") == "PASS"
    return verdict_a and verdict_b


def main():
    head_sha = get_git_head_sha()
    print("================================================================================")
    print("      SAGE C2 — DOUBLE BIG JUMP / TRUE PARALLEL EVOLUTION EXECUTION             ")
    print("================================================================================")
    print(f"[*] Exact observed repository HEAD: {head_sha}")
    print("[*] Launching Wave A and Wave B behind a shared concurrency barrier...")
    start_time = time.time()

    results = execute_parallel_waves(run_wave_a, run_wave_b, Barrier(2))

    elapsed = time.time() - start_time
    print(f"\n[*] Parallel Wave Execution Completed in {elapsed:.3f} seconds.")

    rec_a_path = Path("evidence_capture/execution_intelligence_wave_evidence.json")
    rec_b_path = Path("evidence_capture/governance_intelligence_wave_evidence.json")
    if not rec_a_path.exists() or not rec_b_path.exists():
        print("[!] ERROR: One or both evidence receipt files are missing!")
        return 1

    rec_a = json.loads(rec_a_path.read_text(encoding="utf-8"))
    rec_b = json.loads(rec_b_path.read_text(encoding="utf-8"))

    print("\n[+] WAVE A RECEIPT AUDIT:")
    print(f"    - Receipt ID: {rec_a.get('receipt_id')}")
    print(f"    - Exact Git HEAD: {rec_a.get('exact_git_head')}")
    print(f"    - Concurrent Workers: {rec_a.get('concurrent_workers_used')}")
    print(f"    - Rolls-Royce Quality: {rec_a.get('rolls_royce_quality_passed')}")

    print("\n[+] WAVE B RECEIPT AUDIT:")
    print(f"    - Receipt ID: {rec_b.get('receipt_id')}")
    print(f"    - Exact Git HEAD: {rec_b.get('exact_git_head')}")
    print(f"    - Attack Vectors Neutralized: {rec_b.get('attack_vectors_neutralized')}/{rec_b.get('total_attack_vectors_tested')}")
    print(f"    - Anti-Drift Reconciled: {rec_b.get('anti_drift_reconciled')}")
    print(f"    - Verdict: {rec_b.get('fail_closed_verdict')}")

    if any(code != 0 for code in results.values()):
        print("\n[!] DOUBLE BIG JUMP RECONVERGENCE VERDICT: FAIL_CLOSED")
        return 1

    if reconcile_receipts(rec_a, rec_b, head_sha):
        print("\n================================================================================")
        print("      DOUBLE BIG JUMP RECONVERGENCE VERDICT: PASS                              ")
        print("================================================================================")
        return 0

    print("\n[!] DOUBLE BIG JUMP RECONVERGENCE VERDICT: FAIL_CLOSED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
