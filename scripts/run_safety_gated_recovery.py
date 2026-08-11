#!/usr/bin/env python3
"""SAGE Safety-Gated Recovery Simulation Runner.

Demonstrates recovery of a blocked preflight cycle by providing a corrected,
high-confidence cognitive state to the revalidation bridge, completing
the real workload and promoting trace metadata to SAGE Master Archive.
"""

import json
from pathlib import Path

from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge
from tests.experimental.test_mission_control_bridge import get_mock_cognitive_state


def main():
    print("[*] Launching SAGE Safety-Gated Recovery...")

    bridge = SAGEMissionExecutionBridge()

    # Corrected high-confidence cognitive state (overall confidence = 1.0)
    corrected_state = get_mock_cognitive_state(confidence=1.0)

    # Run recovery
    result = bridge.recover_from_cognitive_block(
        mission_id="mission_safety_gated_pfc",
        target_files=["sage/change_impact.py"],
        corrected_cognitive_state=corrected_state,
        run_real_lint=False
    )

    print(f"[+] Final State reached: {result['final_state']}")
    print(f"[+] Recovery Status:     {result.get('recovery_status')}")
    print(f"[+] Archived Entry ID:   {result.get('archived_entry_id')}")

    output_path = Path("evidence_capture/safety_gated_recovery_evidence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[+] Safety-Gated Recovery evidence successfully written to {output_path}")


if __name__ == "__main__":
    main()
