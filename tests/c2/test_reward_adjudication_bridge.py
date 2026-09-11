from pathlib import Path
from sage.c2.reward_adjudication_bridge import request_c2_reward_adjudication
from sage.experimental.airspace.manager import AirspaceManager


def test_request_c2_reward_adjudication(tmp_path: Path) -> None:
    ledger_path = tmp_path / "airspace_ledger.json"
    manager = AirspaceManager(ledger_path)

    sha = "fc768ee91d0d8ee8c153a1bd647f3b784dbccf1c"
    report_payload = {
        "mission_id": "mission-bridge-001",
        "protocol": "SAGE-SEP/1",
        "subject": {
            "repository": "dariusbrandon880-art/Sage",
            "commit": sha,
        },
        "target_sha": sha,
        "observed_sha": sha,
        "claim": {
            "type": "verified_build",
            "statement": "Bridge adjudication test statement",
        },
        "execution": {
            "actor": "MISSION_CONTROL",
            "supporting_agents": ["ENGINEERING_FLIGHT"],
        },
        "verification": {
            "status": "VERIFIED",
        },
        "outcome": {
            "type": "BUILD",
        },
        "reward": {
            "requested": True,
        },
        "contributions": [
            {
                "actor": "MISSION_CONTROL",
                "role": "Director",
                "contribution_type": "Synthesis",
                "share_weight": 1.0,
                "claim_ref": "claim-001",
            }
        ],
        "evidence": ["evidence:bridge-001"],
    }

    result = request_c2_reward_adjudication(
        report_payload=report_payload,
        manager=manager,
        difficulty=3,
        verification_quality=5,
        impact=4,
        reuse=2,
    )

    assert result["mission_id"] == "mission-bridge-001"
    assert result["outcome_point_pool"] > 0
    assert result["xp_minted"] >= 0
    assert result["conservation_check_passed"] is True
    assert ledger_path.exists()
