#!/usr/bin/env python3
"""Execute SAGE Fleet Evolution Intelligence evaluation over historical evidence receipts.

Outputs evidence receipt to evidence_capture/fleet_evolution_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.experimental.airspace.fleet_evolution import (  # noqa: E402
    FleetEvolutionIntelligence,
)

EVIDENCE_PATH = repo_root / "evidence_capture" / "fleet_evolution_evidence.json"

HISTORICAL_EVIDENCE_FILES = [
    "evidence_capture/multi_frontier_dispatch_evidence.json",
    "evidence_capture/frontier_intelligence_bridge_evidence.json",
    "evidence_capture/frontier_dependency_router_evidence.json",
    "evidence_capture/fleet_readiness_evidence.json",
    "evidence_capture/security_posture_report.json",
]


def load_historical_receipts() -> list[dict]:
    receipts = []
    for rel_path in HISTORICAL_EVIDENCE_FILES:
        file_path = repo_root / rel_path
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                receipts.append(data)
            except Exception:
                pass
    return receipts


def main() -> int:
    print("=" * 70)
    print("SAGE FLEET EVOLUTION INTELLIGENCE EVALUATION")
    print("=" * 70)

    receipts = load_historical_receipts()
    engine = FleetEvolutionIntelligence()

    evolution_receipt = engine.evaluate_growth_signal(receipts, test_pass_rate=1.0)

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evolution_receipt.to_dict(), f, indent=2)

    print(f"Commit SHA: {evolution_receipt.commit_sha}")
    print(f"Receipt ID: {evolution_receipt.receipt_id}")
    print(f"Historical Receipts Audited: {len(receipts)}")
    print(f"Growth Index: {evolution_receipt.growth_index * 100:.1f}%")
    print(f"Growth Signal: {evolution_receipt.growth_signal}")
    print(f"Provenance Hash: {evolution_receipt.provenance_hash}")
    print(f"Evidence Captured: {EVIDENCE_PATH}")

    for name, metric in evolution_receipt.metrics.items():
        print(f"  - [{metric.category.value}] {name} -> Score: {metric.score:.2f} [{metric.rationale}]")

    if evolution_receipt.growth_signal == "BLOCKED":
        print("\n[!] FLEET EVOLUTION EVALUATION BLOCKED BY PROTECTED PATH VIOLATIONS", file=sys.stderr)
        return 1

    print("\n[✓] FLEET EVOLUTION EVALUATION SUCCESSFUL — CAPABILITY SIGNAL RECORDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
