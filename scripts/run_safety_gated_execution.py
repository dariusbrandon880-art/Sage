#!/usr/bin/env python3
"""SAGE Safety-Gated Execution Simulation Runner.

Demonstrates the Prefrontal Cortex Cognitive Safety Gate blocking execution when
a low-confidence/unsafe cognitive state is provided to the revalidation bridge.
"""

import json
from pathlib import Path

from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge
from tests.experimental.test_mission_control_bridge import get_mock_cognitive_state


def main():
    print("[*] Launching SAGE Safety-Gated Execution...")

    # Instantiate bridge and low-confidence cognitive state (overall confidence = 0.1)
    bridge = SAGEMissionExecutionBridge()
    unsafe_state = get_mock_cognitive_state(confidence=0.1)

    # Run workload
    result = bridge.execute_revalidation_workload(
        mission_id="mission_safety_gated_pfc",
        target_files=["sage/change_impact.py"],
        run_real_lint=False,
        cognitive_state=unsafe_state
    )

    print(f"[+] Final State reached: {result['final_state']}")
    print(f"[+] Safety Block active: {result.get('cognitive_block', False)}")
    print(f"[+] PFC Evaluation Outcome: {result['pfc_report']['outcome']}")

    output_path = Path("evidence_capture/safety_gated_execution_evidence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[+] Safety-Gated Execution evidence successfully written to {output_path}")


if __name__ == "__main__":
    main()
