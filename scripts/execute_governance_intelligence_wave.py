#!/usr/bin/env python3
"""Execute the Governance Intelligence capability as an explicit mission set."""

import json
import subprocess
import sys
from pathlib import Path

from sage.c2.governance_intelligence import AdversarialRegressionSuite


def get_git_head_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    head = result.stdout.strip()
    if len(head) != 40 or any(c not in "0123456789abcdefABCDEF" for c in head):
        raise RuntimeError(f"Invalid repository HEAD: {head!r}")
    return head


def main():
    head_sha = get_git_head_sha()
    print("[*] Starting Governance Intelligence mission set")
    print(f"    - Exact git HEAD SHA: {head_sha}")

    suite = AdversarialRegressionSuite()
    receipt = suite.execute_governance_intelligence_wave(
        wave_id="wave_governance_intelligence_v1",
        exact_git_head=head_sha,
    )

    output_path = Path("evidence_capture/governance_intelligence_wave_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt.model_dump(), indent=2) + "\n", encoding="utf-8")

    print(f"[+] Receipt ID: {receipt.receipt_id}")
    print(f"    - Attack Vectors Neutralized: {receipt.attack_vectors_neutralized}/{receipt.total_attack_vectors_tested}")
    print(f"    - Anti-Drift Reconciled: {receipt.anti_drift_reconciled}")
    print(f"    - Verdict: {receipt.fail_closed_verdict}")
    return 0 if receipt.fail_closed_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
