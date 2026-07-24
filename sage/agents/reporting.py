"""Agent Validation Reporting for SAGE Agent Workflow Layer v1."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sage.agents.models import AgentIdentity, AgentTask
from sage.core.attestation import CryptographicAttestationProvider


class AgentValidationReporting:
    """Compiles structured, cryptographically-attested validation reports for agent task completions.

    Ensures full compliance with SAGE-RT-KL-002 and ensures audit durability.
    """

    def __init__(self, attestation_provider: Optional[CryptographicAttestationProvider] = None):
        """Initialize reporter."""
        self.attestation = attestation_provider or CryptographicAttestationProvider()

    def generate_validation_report(
        self,
        agent: AgentIdentity,
        task: AgentTask,
        actions_performed: List[str],
        files_changed: List[str],
        tests_completed: List[str],
        validation_status: str,
        architecture_impact: str,
        remaining_risks: List[str],
    ) -> Dict[str, Any]:
        """Compile a complete, cryptographically signed validation report.

        Args:
            agent: Executing agent's identity profile.
            task: Task context.
            actions_performed: Descriptive list of actions executed.
            files_changed: List of relative paths modified.
            tests_completed: List of test cases/suites executed.
            validation_status: Terminal status (e.g., "PASSED_VERIFIED").
            architecture_impact: Assessed system impact statement.
            remaining_risks: Potential residual operational risks.

        Returns:
            The complete validation report dictionary with a secure signature.
        """
        ts = datetime.now(timezone.utc).isoformat()

        report_payload = {
            "task_id": task.task_id,
            "objective_id": task.objective_id,
            "title": task.title,
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "role": agent.role.value,
            "timestamp": ts,
            "actions_performed": actions_performed,
            "files_changed": files_changed,
            "tests_completed": tests_completed,
            "validation_status": validation_status,
            "architecture_impact": architecture_impact,
            "remaining_risks": remaining_risks,
        }

        # Calculate secure cryptographic signature on payload
        signature = self.attestation.sign(report_payload)

        # Build final report package
        validation_report = {
            "report_payload": report_payload,
            "attestation_signature": signature,
            "provider_type": self.attestation.get_provider_type(),
        }

        return validation_report
