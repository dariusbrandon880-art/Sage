#!/usr/bin/env python3
"""SAGE Phase 4 Controlled Evaluation Execution Script.

Runs the multi-agent Scenario A and Scenario B simulations under Option B parameters,
aggregates the validation metrics, and writes the evidence package to evidence_capture/.
"""

import sys
from pathlib import Path

# Add repo root to path to allow imports of sage
sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.experimental.act.phase_4_eval import Phase4EvaluationRunner


def main():
    print("[*] Initiating SAGE Phase 4 Controlled Evaluation Execution...")
    try:
        runner = Phase4EvaluationRunner()
        package = runner.execute_all()
        print(f"[+] Success! Evidence package aggregated under: {runner.output_path}")
        print(f"[+] Aggregate Steps Reduced: {package['aggregate_metrics']['total_steps_reduced']}")
        print(f"[+] Context Recovery Rate: {package['aggregate_metrics']['context_recovery_success_rate']}%")
    except Exception as e:
        print(f"[-] Execution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
