"""SAGE script to run the actual OpenAI Runtime Activation."""

import os
import sys
import json
import time
from pathlib import Path

# Add project root to python path to ensure sage imports work cleanly
sys.path.insert(0, str(Path(__file__).parent.parent))

from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator
from sage.experimental.cognitive.openai_runtime import OpenAICognitiveRuntimeActivator


def run_activation():
    print("======================================================================")
    print("       SAGE OPENAI RUNTIME + COGNITIVE CONTINUITY ACTIVATION          ")
    print("======================================================================\n")

    # 1. Resolve Runtime Configurations and Secrets from Environment
    agent_id = os.getenv("SAGE_AGENT_ID", "openai-runtime-agent")
    auth_token = os.getenv("SAGE_SECURE_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    session_id = os.getenv("SAGE_SESSION_ID", "session_openai_activation_live")

    # Check for missing crucial infrastructure/environment variables
    missing_secrets = []
    if not auth_token:
        missing_secrets.append("SAGE_SECURE_TOKEN")
    if not openai_key:
        missing_secrets.append("OPENAI_API_KEY")

    if missing_secrets:
        error_msg = f"BLOCKED_MISSING_CREDENTIALS: Required Render runtime secrets are missing: {missing_secrets}"
        print(f"[-] {error_msg}")

        # Capture the infrastructure blocker/error report
        blocker_report = {
            "authentication_result": {
                "success": False,
                "message": "Authentication Failed: SAGE_SECURE_TOKEN is missing in the Render environment."
            },
            "agent_registration_result": {
                "success": False,
                "message": "Registration Failed: Missing secure credentials."
            },
            "session_id": session_id,
            "mission_execution_result": {
                "success": False,
                "error_type": "INFRASTRUCTURE_ERROR",
                "message": error_msg
            },
            "validation_result": {
                "success": False,
                "status": "BLOCKED"
            },
            "evidence_artifact_path": "N/A",
            "timestamp": time.time()
        }

        evidence_path = Path("evidence_capture/openai_cognitive_runtime_activation.json")
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(blocker_report, f, indent=2, default=str)

        print(f"\n[+] Infrastructure blocker report written successfully to {evidence_path}.")
        return

    print(f"[*] Initializing SAGE Developer Workflow Orchestrator for session '{session_id}'...")
    orchestrator = DeveloperWorkflowOrchestrator(
        session_id=session_id,
        objective="Verify PFC integration gate"
    )

    activator = OpenAICognitiveRuntimeActivator(orchestrator=orchestrator)

    print(f"[*] Executing secure OpenAI runtime activation handshake and governed cycle...")
    try:
        report = activator.activate_runtime_session(
            agent_id=agent_id,
            auth_token=auth_token,
            task_id="task_openai_runtime_activation_live",
            task_description="Verify PFC integration gate and execute live governed session",
            session_id=session_id
        )

        print("[+] Handshake and PFC validation evaluation completed successfully!")
        print(f"    - Agent Identity resolved: {agent_id}")
        print(f"    - PFC Decision outcome: {report['pfc_decision']['outcome']}")
        print(f"    - Mission Execution status: {report['execution_result']['status']}")

        evidence_path = Path("evidence_capture/openai_cognitive_runtime_activation.json")
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n[+] Live activation evidence package written successfully to {evidence_path}.")

    except Exception as e:
        print(f"[-] Execution Fault: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_activation()
