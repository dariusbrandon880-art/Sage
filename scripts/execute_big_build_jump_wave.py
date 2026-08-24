#!/usr/bin/env python3
"""Script executing and verifying the Big Build Jump Wave Full Frame Controller."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path for standalone script execution
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sage.c2.big_build_jump_wave import (
    BigBuildJumpWaveEngine,
    FlightMission,
    FlightVector,
)


def main() -> None:
    print("=== SAGE C2 BIG BUILD JUMP WAVE FULL FRAME CONTROLLER ===")
    engine = BigBuildJumpWaveEngine()
    now_utc = datetime.now(timezone.utc).isoformat()
    commit_sha = "ed70dc8"

    vectors = (
        FlightVector(
            flight_number=1,
            mission=FlightMission(
                mission_id="m_f1_intelligence",
                frontier_id="frontier_discovery",
                target_subsystem="sage/experimental/sagi_discovery_flight_selector.py",
                objective="Select diversified discovery candidates",
                required_test_suite="tests/experimental/test_sagi_discovery_flight_selector.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=("sagi_discovery",),
        ),
        FlightVector(
            flight_number=2,
            mission=FlightMission(
                mission_id="m_f2_governance",
                frontier_id="security_posture",
                target_subsystem="SECURITY.md",
                objective="Enforce CODEOWNERS and secret scanning policies",
                required_test_suite="tests/test_governance_directives.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=("security_posture",),
        ),
        FlightVector(
            flight_number=3,
            mission=FlightMission(
                mission_id="m_f3_immersion",
                frontier_id="agent_hud_projection",
                target_subsystem="sage/experimental/agent_hud_projection.py",
                objective="Render Command Center identity badges for agent chat interfaces",
                required_test_suite="tests/experimental/test_agent_hud_projection.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=("agent_hud",),
        ),
        FlightVector(
            flight_number=4,
            mission=FlightMission(
                mission_id="m_f4_execution",
                frontier_id="frontier_dependency_router",
                target_subsystem="sage/experimental/frontier_dependency_router.py",
                objective="Route candidates across dependency graphs and affected namespaces",
                required_test_suite="tests/experimental/test_frontier_dependency_router.py",
                authorized=True,
            ),
            risk_level="MEDIUM",
            collision_keys=("dependency_router",),
        ),
        FlightVector(
            flight_number=5,
            mission=FlightMission(
                mission_id="m_f5_warehouse",
                frontier_id="fleet_command_intelligence",
                target_subsystem="sage/experimental/airspace/fleet_command_intelligence.py",
                objective="Track XP, qualification levels, and Big Strike milestone receipts",
                required_test_suite="tests/experimental/test_fleet_command_intelligence.py",
                authorized=True,
            ),
            risk_level="LOW",
            collision_keys=("fleet_command",),
        ),
    )

    wave_receipt = engine.dispatch_and_reconverge(
        "wave_bbjw_2026_08_24", commit_sha, vectors, now_utc
    )

    report = {
        "wave_id": wave_receipt.wave_id,
        "commit_sha": wave_receipt.commit_sha,
        "status": wave_receipt.status.value,
        "collision_status": wave_receipt.collision_status,
        "boundary_status": wave_receipt.boundary_status,
        "validation_status": wave_receipt.validation_status,
        "promotion_status": wave_receipt.promotion_status,
        "receipt_digest": wave_receipt.receipt_digest,
        "timestamp_utc": wave_receipt.timestamp_utc,
        "flights_count": len(wave_receipt.flight_receipts),
    }

    print(json.dumps(report, indent=2))

    if wave_receipt.validation_status != "PASS":
        print("Big Build Jump Wave Execution Failed!")
        sys.exit(1)

    print("Big Build Jump Wave Execution Successful & Reconverged!")


if __name__ == "__main__":
    main()
