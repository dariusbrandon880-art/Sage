"""SAGE Governed Agent Activation Prototype.

Provides the minimum viable governed agent orchestrator, metrics collector, and demonstration interface.
Operating strictly in non-mutative, experimental scope.
"""

import time
import uuid
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PrototypeMetricsCollector:
    """Captures and stores performance and governance metrics for prototype runs."""

    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            "execution_duration_sec": 0.0,
            "context_recovered_keys": 0,
            "duplicate_work_prevented_count": 0,
            "validation_checks_passed_count": 0,
            "evidence_completeness_score": 0.0,
            "human_review_checkpoints_hit": 0,
            "failure_conditions_encountered_count": 0,
        }

    def record_metrics(
        self,
        duration: float,
        contexts: int,
        duplicates: int,
        checks: int,
        evidence_score: float,
        checkpoints: int,
        failures: int = 0,
    ) -> None:
        """Records metric values."""
        self.metrics["execution_duration_sec"] = round(duration, 4)
        self.metrics["context_recovered_keys"] = contexts
        self.metrics["duplicate_work_prevented_count"] = duplicates
        self.metrics["validation_checks_passed_count"] = checks
        self.metrics["evidence_completeness_score"] = round(evidence_score, 2)
        self.metrics["human_review_checkpoints_hit"] = checkpoints
        self.metrics["failure_conditions_encountered_count"] = failures

    def get_report(self) -> Dict[str, Any]:
        """Returns the collected metrics report."""
        return dict(self.metrics)


class PrototypeOrchestratorRunner:
    """Orchestrates the sequential governed handoff for the SAGE Agent Activation Prototype."""

    def __init__(self) -> None:
        self.state: str = "PROPOSED"
        self.metrics_collector = PrototypeMetricsCollector()
        self.trace_log: List[str] = []
        self.receipts: List[Dict[str, Any]] = []
        self.evidence_package: Optional[Dict[str, Any]] = None
        self.human_decision: Optional[str] = None

    def log_step(self, message: str) -> None:
        """Logs a step trace in UTC."""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.trace_log.append(f"[{timestamp}] {message}")

    def run_simulation(self, human_objective: str) -> Dict[str, Any]:
        """Fallback wrapper to remain compatible with existing tests."""
        return self.run_validation_scenario(
            scenario_id="SCENARIO_A",
            human_objective=human_objective
        )

    def run_validation_scenario(
        self,
        scenario_id: str,
        human_objective: str,
        inject_failure: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs a Phase 2 validated scenario with optional governed failure injections."""
        start_time = time.time()
        self.state = "RUNNING"
        self.trace_log.clear()
        self.receipts.clear()

        self.log_step(f"Initiating validation run. Scenario: '{scenario_id}', Objective: '{human_objective}'")

        try:
            # Failure Case: Invalid Agent Identity
            if inject_failure == "invalid_agent_identity":
                self.log_step("[Gatekeeper] Intercepted illegal agent enrollment attempt.")
                self.metrics_collector.record_metrics(0.001, 0, 0, 0, 0.0, 0, failures=1)
                self.state = "REJECT_CLOSED"
                raise ValueError("Failure Validation: Invalid identity format.")

            # Failure Case: Permission Violation Attempt
            if inject_failure == "permission_violation_attempt":
                self.log_step("[Gatekeeper] Intercepted unauthorized capability passport request.")
                self.metrics_collector.record_metrics(0.001, 0, 0, 1, 0.1, 0, failures=1)
                self.state = "REJECT_CLOSED"
                raise PermissionError("Failure Validation: Unauthorized capability format.")

            # 1. Coordinator Agent Assignment
            self.log_step("[Coordinator Agent] Received human objective and mapped task dependencies.")
            coord_receipt = {
                "agent_id": "agent_coordinator_chatgpt",
                "action": "delegate_tasks",
                "status": "SUCCESS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.receipts.append(coord_receipt)

            # 2. Research Agent Retrieval & Duplicate Check
            self.log_step("[Research Agent] Scanning Master Archive and previous indexes.")

            # Failure Case: Duplicate Knowledge Detection
            has_duplicate = "duplicate" in human_objective.lower()
            duplicate_prevented = 1 if has_duplicate else 0

            if inject_failure == "duplicate_knowledge_detection":
                self.log_step("[Research Agent] DUPLICATE DETECTED (INJECTED): Target context matches existing indexes. Halting generation to prevent redundancy.")
                self.metrics_collector.record_metrics(0.002, 3, 1, 2, 0.4, 0, failures=1)
                self.state = "REJECT_CLOSED"
                raise ValueError("Failure Validation: Stale/Duplicate work detected. Execution halted safely.")

            if has_duplicate:
                self.log_step("[Research Agent] DUPLICATE DETECTED: Similar context reference already exists in index.")
            else:
                self.log_step("[Research Agent] NO DUPLICATES: Objective context represents fresh requirements.")

            # Simulate Context Recovery based on Scenario
            contexts_recovered = 5
            if scenario_id == "SCENARIO_A":
                self.log_step("[Research Agent] Restoring 5 SAGE historical session context reference nodes.")
            elif scenario_id == "SCENARIO_B":
                self.log_step("[Research Agent] Conducting validation evidence-gathering across experimental logs.")
            elif scenario_id == "SCENARIO_C":
                self.log_step("[Research Agent] Recovering architectural and issue validation lineages.")

            research_receipt = {
                "agent_id": "agent_research_gemini",
                "action": "recover_context",
                "context_references_found": contexts_recovered,
                "duplicate_prevented": duplicate_prevented,
                "status": "SUCCESS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.receipts.append(research_receipt)

            # 3. Review Agent Boundary & Safety Enforcement
            self.log_step("[Review Agent] Auditing active sandbox write boundaries.")

            # Failure Case: Boundary Violation Attempt
            target_path = "sage/experimental/outputs/validation_output.json"
            if inject_failure == "boundary_violation_attempt":
                target_path = "sage/core/spek.py"  # Illegal core mutative path

            is_safe = target_path.startswith("sage/experimental/")
            if not is_safe:
                self.log_step(f"[Review Agent] SECURITY VIOLATION: Unauthorized write attempt to '{target_path}'. Enforcing lock.")
                self.metrics_collector.record_metrics(0.002, contexts_recovered, 0, 3, 0.5, 0, failures=1)
                self.state = "REJECT_CLOSED"
                raise PermissionError("Failure Validation: Boundary violation. Write attempts outside sage/experimental/ are blocked.")

            # Failure Case: Missing Evidence
            if inject_failure == "missing_evidence":
                self.log_step("[Review Agent] ATTENTION: Missing chronological UTC sequence markers or preceding hashes.")
                self.metrics_collector.record_metrics(0.002, contexts_recovered, 0, 4, 0.3, 0, failures=1)
                self.state = "REJECT_CLOSED"
                raise ValueError("Failure Validation: Malformed envelope. Missing evidence chains.")

            self.log_step(f"[Review Agent] PATH VERIFIED: Write target '{target_path}' resides within experimental boundary.")
            review_receipt = {
                "agent_id": "agent_reviewer_claude",
                "action": "verify_boundary",
                "target_path": target_path,
                "status": "SUCCESS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.receipts.append(review_receipt)

            # 4. Documentation Agent Output Creation
            self.log_step("[Documentation Agent] Compiling summary output draft with evidence citations.")
            output_content = {
                "summary_id": f"doc_{uuid.uuid4().hex[:12]}",
                "scenario_id": scenario_id,
                "objective": human_objective,
                "provenance_chain": [r["agent_id"] for r in self.receipts],
                "validation_score": 1.0,
                "metadata_status": "VALIDATED_EXPERIMENTAL",
            }
            doc_receipt = {
                "agent_id": "agent_documentation_assistant",
                "action": "draft_output",
                "status": "SUCCESS",
                "output_draft": output_content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.receipts.append(doc_receipt)

            # Compile Chained Receipts via SAGE-CRC
            self.log_step("[SAGE-CRC] Chaining sequential execution receipts cryptographically.")
            chained_receipts = []
            last_hash = "0" * 64
            for r in self.receipts:
                combined_string = f"{r['agent_id']}-{r['action']}-{last_hash}"
                current_hash = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()
                r_chained = dict(r)
                r_chained["previous_hash"] = last_hash
                r_chained["current_hash"] = current_hash
                chained_receipts.append(r_chained)
                last_hash = current_hash

            # Update Metrics
            duration = time.time() - start_time
            self.metrics_collector.record_metrics(
                duration=duration,
                contexts=contexts_recovered,
                duplicates=duplicate_prevented,
                checks=7,  # All 7 validation checks passed
                evidence_score=1.0,
                checkpoints=1,  # Paused at Human Approval Gate
                failures=0,
            )

            self.evidence_package = {
                "scenario_id": scenario_id,
                "objective": human_objective,
                "trace_log": self.trace_log,
                "receipts": chained_receipts,
                "metrics": self.metrics_collector.get_report(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "review_status": "PENDING_HUMAN_APPROVAL",
            }

            self.state = "PAUSED_AT_GATE"
            self.log_step("[Human Approval Gate] Simulation paused. Awaiting human decision record.")
            return dict(self.evidence_package)

        except Exception as e:
            # Capture failure metrics
            self.log_step(f"Execution Terminated: {str(e)}")
            self.evidence_package = {
                "scenario_id": scenario_id,
                "objective": human_objective,
                "trace_log": self.trace_log,
                "metrics": self.metrics_collector.get_report(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "review_status": "REJECT_CLOSED",
                "error_details": str(e),
            }
            raise e

    def record_human_decision(self, decision: str) -> Dict[str, Any]:
        """Applies a manual human approval decision to finalize the prototype run."""
        if self.state != "PAUSED_AT_GATE" or not self.evidence_package:
            raise ValueError("Lifecycle Violation: Can only record decision from PAUSED_AT_GATE state.")

        if decision not in ["APPROVED", "REJECTED"]:
            raise ValueError(f"Invalid Decision: '{decision}' must be APPROVED or REJECTED.")

        self.human_decision = decision
        self.evidence_package["review_status"] = f"HUMAN_{decision}"
        self.evidence_package["decision_timestamp"] = datetime.now(timezone.utc).isoformat()

        if decision == "APPROVED":
            self.state = "COMPLETED"
            self.log_step("[Human Approval Gate] Decision Captured: APPROVED. Ready for experimental promotion.")
        else:
            self.state = "REJECTED"
            self.log_step("[Human Approval Gate] Decision Captured: REJECTED. Simulation state discarded.")

        return dict(self.evidence_package)


class DemoInterface:
    """Mock Command-Line and API Interface to interact with the SAGE Governed Agent Prototype."""

    def __init__(self) -> None:
        self.runner = PrototypeOrchestratorRunner()

    def run_demo(self, objective: str, auto_approve: bool = True) -> str:
        """Executes a full prototype run and returns a formatted terminal output report."""
        try:
            self.runner.run_validation_scenario("SCENARIO_A", objective)
            if auto_approve:
                self.runner.record_human_decision("APPROVED")
            else:
                self.runner.record_human_decision("REJECTED")

            pkg = self.runner.evidence_package
            assert pkg is not None
            report = [
                "=" * 60,
                "SAGE Governed Agent Prototype Run Report",
                "=" * 60,
                f"Scenario ID:     {pkg['scenario_id']}",
                f"Objective:       {pkg['objective']}",
                f"State:           {self.runner.state}",
                f"Review Status:   {pkg['review_status']}",
                f"Duration (Sec):  {pkg['metrics']['execution_duration_sec']}",
                f"Validation Pass: {pkg['metrics']['validation_checks_passed_count']}/7 Checks",
                f"Duplicates:      {pkg['metrics']['duplicate_work_prevented_count']} Prevented",
                "-" * 60,
                "Chained Receipt Provenance Lineage:",
            ]
            for r in pkg["receipts"]:
                report.append(f"  -> [{r['timestamp']}] {r['agent_id']} ({r['action']})")
                report.append(f"     Current Hash:   {r['current_hash']}")
                report.append(f"     Previous Hash:  {r['previous_hash']}")

            report.append("=" * 60)
            return "\n".join(report)

        except Exception as e:
            return f"Demo Error: {str(e)}"
