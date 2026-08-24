#!/usr/bin/env python3
"""Runner script to execute the Adaptive Mission Selection Engine.

Evaluates sample discovery proposals across current frontiers and persists evidence receipt to
evidence_capture/adaptive_mission_selection_evidence.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine


def main() -> None:
    print("================================================================================")
    print("SAGE C2 — ADAPTIVE MISSION SELECTION EXECUTION")
    print("================================================================================")

    engine = AdaptiveMissionSelectionEngine()
    print(f"Commit SHA: {engine.commit_sha}\n")

    sample_proposals = [
        {
            "candidate_id": "cand_001_continuity_projection",
            "proposal_title": "Continuity Projection & Archive Rehydration Sync",
            "target_lane": "Lane 1: Continuity Projection",
            "target_paths": ["sage/experimental/act/continuity_control.py"],
            "base_priority": 1.5,
            "c2_authorization_token": "C2-AUTH-TOK-20260824-CONTINUITY",
        },
        {
            "candidate_id": "cand_002_governed_execution",
            "proposal_title": "End-to-End Governed Execution Assembly Line",
            "target_lane": "Lane 2: Governed Execution",
            "target_paths": ["sage/experimental/airspace/fleet_readiness.py"],
            "base_priority": 1.4,
            "c2_authorization_token": "C2-AUTH-TOK-20260824-EXECUTION",
        },
        {
            "candidate_id": "cand_003_scientific_robustness",
            "proposal_title": "Sports Research Substrate Out-of-Sample Separator",
            "target_lane": "Lane 3: Sports Research Robustness",
            "target_paths": ["sage/experimental/sports_longitudinal.py"],
            "base_priority": 1.2,
            "c2_authorization_token": None,  # No C2 token -> fail-closed unapproved
        },
        {
            "candidate_id": "cand_004_core_runtime_mutation_attempt",
            "proposal_title": "Unauthorized Core Engine Optimization",
            "target_lane": "Protected Core Frontier",
            "target_paths": ["sage/core/engine.py"],  # Touches protected core -> falsified
            "base_priority": 2.0,
            "c2_authorization_token": "C2-AUTH-TOK-20260824-UNAUTHORIZED",
        },
    ]

    print("Evaluating discovery proposals...")
    receipt = engine.select_and_rank_candidates(sample_proposals)

    for packet in receipt.decision_packets:
        print(f"[{packet.candidate_id}] {packet.proposal_title}")
        print(f"  Target Lane: {packet.target_lane}")
        print(f"  Priority Score: {packet.priority_score:.2f} | Risk Score: {packet.risk_score:.2f}")
        print(f"  Is Authorized: {packet.is_authorized} | Falsification Verdict: {packet.falsification_verdict}")
        print(f"  Provenance SHA-256: {packet.provenance_hash}\n")

    print(f"Total Evaluated: {receipt.total_candidates_evaluated}")
    print(f"Authorized Count: {receipt.authorized_candidates_count}")
    print(f"Selection Verdict: {receipt.selection_verdict}")

    evidence_dir = REPO_ROOT / "evidence_capture"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_file = evidence_dir / "adaptive_mission_selection_evidence.json"

    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    print(f"\nPersisted evidence receipt to {evidence_file}")
    print("================================================================================")


if __name__ == "__main__":
    main()
