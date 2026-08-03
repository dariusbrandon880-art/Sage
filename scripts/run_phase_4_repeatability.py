#!/usr/bin/env python3
"""SAGE Phase 4 Repeatability Validation Runner Script.

Executes 5 sequential multi-agent simulation runs, calculates mean and variance
metrics, performs trace checks, and dumps aggregate stats to evidence_capture/.
"""

import sys
from pathlib import Path

# Add repo root to path to allow imports of sage
sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.experimental.act.phase_4_repeatability import Phase4RepeatabilityRunner


def main():
    print("[*] Initiating SAGE Phase 4 Repeatability Validation Execution...")
    try:
        runner = Phase4RepeatabilityRunner(num_runs=5)
        summary = runner.execute_repeatability_suite()
        print("[+] Success! SAGE Repeatability validation complete.")
        print(f"[+] Total runs executed: {summary['total_runs_executed']}")
        print(f"[+] Success Rate: {summary['success_rate_percent']}%")
        stats = summary["repeatability_statistics"]["total_duration_mins"]
        print(f"[+] Execution Time Mean: {stats['mean']} mins (Variance: {stats['variance']})")
    except Exception as e:
        print(f"[-] Repeatability Execution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
