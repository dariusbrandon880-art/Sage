#!/usr/bin/env python3
"""Execute Boss Fight #1 Reward Adjudication under SAGE-RP-1.0 (Issue #426).

This script constructs the machine-readable SEP/1 Evidence Packet for Boss Fight #1
(Queue #10 settlement defect repair), passes it to the autonomous SAGE RewardAdjudicator,
prints the canonical SAGE REWARD RECEIPT, and persists evidence to evidence_capture/.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.experimental.airspace.manager import AirspaceManager
from sage.experimental.airspace.reward_protocol import RewardAdjudicator, SAGEEvidencePacket, RewardRequest


def main() -> None:
    print("=== SAGE REWARD ADJUDICATOR: BOSS FIGHT #1 (ISSUE #426) ===")

    target_sha = "75c583db46bb90cc2af925f807e1809bd7023f12"
    evidence_refs = [
        "exact_head_ci",
        "pull_request",
        "repaired_test",
        "canonical_points_xp_authority",
    ]
    digest_bytes = hashlib.sha256(f"BOSS-0001:{target_sha}:{':'.join(evidence_refs)}".encode("utf-8")).hexdigest()

    # 1. Construct Boss Fight #1 machine-readable evidence packet (SEP/1)
    report_payload = {
        "protocol": "SAGE-SEP/1",
        "mission_id": "BOSS-0001",
        "subject": {
            "repository": "dariusbrandon880-art/Sage",
            "commit": target_sha,
        },
        "claim": {
            "type": "verified_repair",
            "statement": "Queue #10 settlement defect repaired",
        },
        "execution": {
            "actor": "CHATGPT_C2",
            "supporting_agents": ["JULES", "GEMINI"],
        },
        "contributions": [
            {
                "actor": "CHATGPT_C2",
                "role": "MISSION_CONTROL",
                "contribution_type": "TARGET_IDENTIFICATION_AND_REPAIR_DIRECTION",
                "share_weight": 0.5,
                "claim_ref": "BOSS-0001:c2",
            },
            {
                "actor": "JULES",
                "role": "EXECUTION_BUILDER",
                "contribution_type": "IMPLEMENTATION_AND_TEST_HARNESS",
                "share_weight": 0.3,
                "claim_ref": "BOSS-0001:jules",
            },
            {
                "actor": "GEMINI",
                "role": "RECON_PROBE",
                "contribution_type": "ADVERSARIAL_RECONNAISSANCE",
                "share_weight": 0.2,
                "claim_ref": "BOSS-0001:gemini",
            },
        ],
        "evidence": evidence_refs,
        "verification": {
            "status": "VERIFIED",
        },
        "outcome": {
            "type": "BOSS_KILL",
            "boss_class": "BIG",
        },
        "integrity": {
            "digest": f"sha256:{digest_bytes}",
        },
        "reward": {
            "requested": True,
        },
    }

    pkt = SAGEEvidencePacket.parse_report_payload(report_payload)
    request = RewardRequest(
        evidence_packet=pkt,
        difficulty=1,
        verification_quality=1,
        impact=1,
        reuse=1,
    )

    manager = AirspaceManager(ledger_path=Path("evidence_capture/boss_fight_1_airspace_ledger.json"))
    decision = RewardAdjudicator.adjudicate(request, manager)

    print("\n" + decision.receipt_header_text + "\n")

    sagi_signal = RewardAdjudicator.build_sagi_learning_signal(decision)
    print("SAGI Learning Signal:")
    print(json.dumps(sagi_signal, indent=2))

    # Test idempotency on replay
    replay_decision = RewardAdjudicator.adjudicate(request, manager)
    assert replay_decision.settlement_id == decision.settlement_id
    assert replay_decision.xp_minted == 0, "Replay must not double-mint XP"
    print("\nIdempotency check: PASSED (Replay yielded exact settlement without double-minting)")

    out_dir = Path("evidence_capture")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "boss_fight_1_reward_evidence.json"
    evidence_payload = {
        "decision": decision.model_payload(),
        "sagi_signal": sagi_signal,
    }
    out_file.write_text(json.dumps(evidence_payload, indent=2), encoding="utf-8")
    print(f"\nPersisted Boss Fight #1 evidence to {out_file}")


if __name__ == "__main__":
    main()
