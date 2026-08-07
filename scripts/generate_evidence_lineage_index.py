#!/usr/bin/env python3
"""CLI Script to compile and generate the SAGE Evidence Lineage Index."""

import sys
from pathlib import Path

# Resolve project root dynamically to allow direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.experimental.evidence_lineage import EvidenceLineageTracker


def main():
    print("==================================================================")
    print("      SAGE EVIDENCE LINEAGE INDEX COMPILER                       ")
    print("==================================================================\n")

    tracker = EvidenceLineageTracker()
    out_path = tracker.generate_and_save()

    print(f"\n[+] Lineage Compilation Complete! Saved to: {out_path}")


if __name__ == "__main__":
    main()
