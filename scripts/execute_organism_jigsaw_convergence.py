#!/usr/bin/env python3
"""Runner script to execute full Organism Jigsaw Convergence verification and persist evidence receipt."""

import json
import sys
from pathlib import Path

from sage.c2.organism_jigsaw import OrganismJigsawEngine


def main() -> None:
    print("[SAGE::C2::ORGANISM] Executing Organism Jigsaw Convergence Verification...")
    engine = OrganismJigsawEngine()
    receipt = engine.execute()

    if not receipt.verify():
        print("ERROR: Organism Jigsaw verification receipt cryptographic verification failed!", file=sys.stderr)
        sys.exit(1)

    if not receipt.all_gates_passed:
        print(f"ERROR: Organism Jigsaw verification failed. Duplicate authorities: {receipt.duplicate_authorities_detected}, Gates passed: {receipt.gates_passed}/{receipt.gates_evaluated}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path("evidence_capture")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "organism_jigsaw_evidence.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(receipt.model_dump(), f, indent=2)

    print(f"SUCCESS: Organism Jigsaw Convergence Verified.")
    print(f"Commit SHA: {receipt.commit_sha}")
    print(f"Subsystems Registered: {receipt.subsystem_count}")
    print(f"Duplicate Authorities: {receipt.duplicate_authorities_detected}")
    print(f"Connective Tissue Gates Passed: {receipt.gates_passed}/{receipt.gates_evaluated}")
    print(f"Evidence Receipt Hash: {receipt.receipt_hash}")
    print(f"Evidence Receipt Persisted: {output_path}")


if __name__ == "__main__":
    main()
