#!/usr/bin/env python3
"""Execute Governance Intelligence as an explicit mission set."""
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
    receipt = AdversarialRegressionSuite().execute_governance_intelligence_wave(
        wave_id="wave_governance_intelligence_v1", exact_git_head=head_sha
    )
    output_path = Path("evidence_capture/governance_intelligence_wave_evidence.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt.model_dump(), indent=2) + "\n", encoding="utf-8")
    return 0 if receipt.fail_closed_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
