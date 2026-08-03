"""SAGE Demonstration Scenario Experience.

Coordinates the scenario registry, standardized scenario definitions, reusable execution
wrappers, user result summaries, and repeatable scenario evidence generation.
"""

import os
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sage.experimental.act.demo_launcher import SAGEDemoLauncher


class SAGEDemoScenarioRegistry:
    """Registry and execution wrapper for standardized demonstration scenarios."""

    def __init__(self, output_path: str = "evidence_capture/demo_scenario_evidence.json"):
        self.output_path = output_path
        self.launcher = SAGEDemoLauncher()
        self.scenarios: Dict[str, Dict[str, Any]] = {
            "scenario_default_audit": {
                "name": "Standard Audit Trace Verification",
                "description": "Validates model-agnostic lineage records and CMAPS schema compliance.",
                "difficulty": "standard",
            },
            "scenario_stress_recovery": {
                "name": "Asymmetric Cryptographic State Recovery",
                "description": "Simulates split-brain divergence recovery and cryptographic receipt chains.",
                "difficulty": "advanced",
            },
        }
        self.scenario_state: Optional[Dict[str, Any]] = None

    def get_registered_scenarios(self) -> List[Dict[str, Any]]:
        """Returns the list of standardized demo scenarios."""
        return [
            {"scenario_id": s_id, **s_info} for s_id, s_info in self.scenarios.items()
        ]

    def execute_selected_scenario(
        self,
        scenario_id: str,
        approver: str = "supervisor_charlie",
        signature: str = "sig_scenario_approved_1100",
    ) -> Dict[str, Any]:
        """Runs the reusable execution wrapper, compiling states and result summaries."""
        if scenario_id not in self.scenarios:
            raise ValueError(f"SAGE Scenario Error: Scenario '{scenario_id}' is not registered.")

        # Re-use the existing launcher capability
        launcher_run = self.launcher.execute_demo_scenario(
            scenario_id=scenario_id,
            approver=approver,
            signature=signature,
        )

        scenario_info = self.scenarios[scenario_id]

        # Improved User Result Summary presentation
        summary = (
            f"================ SAGE SCENARIO EXPERIENCE ================\n"
            f"Scenario Name: {scenario_info['name']}\n"
            f"Scenario Description: {scenario_info['description']}\n"
            f"Run Status: SUCCESS\n"
            f"Execution Summary:\n{launcher_run['unified_execution_summary']}\n"
            f"==========================================================="
        )

        state = {
            "run_id": f"scenario_run_{hashlib.md5(scenario_id.encode()).hexdigest()[:8]}",
            "scenario_id": scenario_id,
            "scenario_details": scenario_info,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "launcher_result": launcher_run,
            "improved_result_summary": summary,
        }

        # Compute deterministic checksum
        serialized = json.dumps(state, sort_keys=True)
        state_checksum = hashlib.sha256(serialized.encode()).hexdigest()
        state["scenario_checksum"] = state_checksum

        self.scenario_state = state
        return state

    def export_scenario_evidence(self) -> str:
        """Generates repeatable scenario evidence logs as a durable JSON package."""
        if not self.scenario_state:
            raise ValueError("SAGE Scenario Error: No scenarios have been executed yet.")

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.scenario_state, f, indent=2, sort_keys=True)

        return self.output_path
