#!/usr/bin/env python3
"""Script executing and verifying the C2 Build Jump Wave Dispatch Engine."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path for standalone script execution
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sage.c2.build_jump_wave import (
    BuildJumpWaveDispatchEngine,
    FlightVectorTarget,
    WaveStatus,
)


def main() -> None:
    print("=== SAGE C2 BUILD JUMP WAVE DISPATCH ENGINE ===")
    engine = BuildJumpWaveDispatchEngine()
    now_utc = datetime.now(timezone.utc).isoformat()
    commit_sha = "ed70dc8"

    targets = (
        FlightVectorTarget(
            flight_id="F1_FOUNDATION",
            path_number=1,
            course_part=1,
            mission_objective="Load repository state and verify main branch lineage",
            target_module="sage/c2/frontier_execution.py",
            required_test_suite="tests/test_c2_five_fronts.py",
            authorized=True,
        ),
        FlightVectorTarget(
            flight_id="F2_INTELLIGENCE",
            path_number=2,
            course_part=2,
            mission_objective="Perform candidate dependency routing and risk analysis",
            target_module="sage/experimental/frontier_dependency_router.py",
            required_test_suite="tests/experimental/test_frontier_dependency_router.py",
            authorized=True,
        ),
        FlightVectorTarget(
            flight_id="F3_EXECUTION",
            path_number=3,
            course_part=3,
            mission_objective="Execute governed builds with fail-closed authorization bounds",
            target_module="sage/experimental/airspace/fleet_command_intelligence.py",
            required_test_suite="tests/experimental/test_fleet_command_intelligence.py",
            authorized=True,
        ),
        FlightVectorTarget(
            flight_id="F4_VERIFICATION",
            path_number=4,
            course_part=4,
            mission_objective="Evaluate evidence-backed fleet readiness and security posture",
            target_module="sage/experimental/airspace/fleet_readiness.py",
            required_test_suite="tests/experimental/test_fleet_readiness.py",
            authorized=True,
        ),
        FlightVectorTarget(
            flight_id="F5_WAREHOUSE",
            path_number=5,
            course_part=4,
            mission_objective="Package reusable assets and project Command Center identity badges",
            target_module="sage/experimental/agent_hud_projection.py",
            required_test_suite="tests/experimental/test_agent_hud_projection.py",
            authorized=True,
        ),
    )

    status, receipts = engine.dispatch_wave("wave_bjw_2026_08_24", commit_sha, targets, now_utc)
    print(f"Wave Dispatch Status: {status.value}")

    wave_receipt = engine.reconverge_wave("wave_bjw_2026_08_24", commit_sha, receipts, now_utc)

    report = {
        "wave_id": wave_receipt.wave_id,
        "commit_sha": wave_receipt.commit_sha,
        "status": wave_receipt.status.value,
        "verdict": wave_receipt.reconvergence_verdict,
        "receipt_digest": wave_receipt.receipt_digest,
        "timestamp_utc": wave_receipt.timestamp_utc,
        "flights_count": len(wave_receipt.flight_receipts),
    }

    print(json.dumps(report, indent=2))

    if wave_receipt.reconvergence_verdict != "PASS":
        print("Build Jump Wave Execution Failed!")
        sys.exit(1)

    print("Build Jump Wave Execution Successful & Reconverged!")


if __name__ == "__main__":
    main()
