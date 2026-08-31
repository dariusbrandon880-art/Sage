#!/usr/bin/env python3
"""Execute Wave B — Governance Intelligence Big Jump Wave."""

import json
import re
import subprocess
import sys
from pathlib import Path

from sage.c2.governance_intelligence import AdversarialRegressionSuite


def get_git_head_sha() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    sha = res.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise ValueError(f"Invalid exact git HEAD commit SHA: {sha}")
    return sha


def main():
    head_sha = get_git_head_sha()
    print("[*] Starting Wave B (Governance Intelligence) Execution...")
    print(f"    - Exact git HEAD SHA: {head_sha}")

    suite = AdversarialRegressionSuite()
    receipt = suite.execute_governance_intelligence_wave(
        wave_id="wave_governance_intelligence_v1",
        exact_git_head=head_sha,
    )

    output_path = Path("evidence_capture/governance_intelligence_wave_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt.model_dump(), indent=2), encoding="utf-8")

    print("[+] Wave B Completed Cleanly!")
    print(f"    - Receipt ID: {receipt.receipt_id}")
    print(f"    - Attack Vectors Neutralized: {receipt.attack_vectors_neutralized}/{receipt.total_attack_vectors_tested}")
    print(f"    - Anti-Drift Reconciled: {receipt.anti_drift_reconciled}")
    print(f"    - Verdict: {receipt.fail_closed_verdict}")
    print(f"    - Evidence saved to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
