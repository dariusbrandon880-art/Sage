"""SAGE State Transition Protocol (STP) - transactional state mutation and rollback engine."""

from typing import Callable, Dict, Any
from datetime import datetime, timezone


class StateTransitionProtocol:
    """Manages transactional state changes (S0 -> Delta -> Evidence -> Validation -> S1).

    Automatically executes a rollback to S0 on validation or execution failures.
    """

    def __init__(self, runtime_engine):
        self.runtime = runtime_engine

    def execute_transition(
        self, mutation_func: Callable[[], Any], transition_name: str
    ) -> Dict[str, Any]:
        """Transactionally executes a state mutation with automatic rollback on validation failure.

        Steps:
        1. Capture current state snapshot (S0)
        2. Attempt state mutation (Delta)
        3. Perform evidence-based self-verification (Validation Gate)
        4. If valid, commit changes (S1) and save checkpoint
        5. If invalid, execute rollback to S0 and record a reliability incident

        Args:
            mutation_func: Callable executing the state change
            transition_name: High-level descriptive name of the transition

        Returns:
            Dict containing transition outcome, status, and generated checkpoint or errors.
        """
        if not self.runtime:
            return {"success": False, "error": "No active runtime engine."}

        # Step 1: Capture original state (S0) via temporary checkpoint/snapshot
        s0_snapshot_id = self.runtime.create_workspace_snapshot()
        datetime.now(timezone.utc)

        try:
            # Step 2: Attempt state mutation (Delta)
            mutation_func()
        except Exception as e:
            # Handle execution failure: Rollback immediately
            self.runtime.restore_workspace_snapshot(s0_snapshot_id)
            # Log reliability incident
            incident_id = None
            if hasattr(self.runtime, "validation") and hasattr(self.runtime.validation, "memory"):
                from sage.validation import ReliabilityIncidentTracker

                tracker = ReliabilityIncidentTracker(self.runtime.memory)
                incident_id = tracker.record_incident(
                    incident_type="exception",
                    description=f"STP Transition '{transition_name}' execution failed: {str(e)}",
                    metadata={"transition_name": transition_name, "error": str(e)},
                )

            return {
                "success": False,
                "status": "execution_failed_rolled_back",
                "error": str(e),
                "incident_id": incident_id,
                "restored_snapshot": s0_snapshot_id,
            }

        # Step 3: Validation Gate - Perform evidence-based self-verification
        integrity_report = self.runtime.verify_integrity()
        is_valid = integrity_report.get("is_valid", False)

        if is_valid:
            # Step 4: Validation succeeded - Commit changes (S1), checkpoint, and snapshot
            checkpoint_id = self.runtime.checkpoint()
            s1_snapshot_id = self.runtime.create_workspace_snapshot()

            # Log recent change in context tracker
            if hasattr(self.runtime, "context_tracker"):
                self.runtime.context_tracker.add_recent_change(
                    f"STP Transition '{transition_name}' succeeded. Committed S1 checkpoint '{checkpoint_id}'."
                )

            return {
                "success": True,
                "status": "committed_s1",
                "transition_name": transition_name,
                "checkpoint_id": checkpoint_id,
                "snapshot_id": s1_snapshot_id,
                "integrity_report": integrity_report,
            }
        else:
            # Step 5: Validation failed - Execute rollback to S0
            self.runtime.restore_workspace_snapshot(s0_snapshot_id)

            # Record a structured reliability incident
            incident_id = None
            if hasattr(self.runtime, "validation") and hasattr(self.runtime.validation, "memory"):
                from sage.validation import ReliabilityIncidentTracker

                tracker = ReliabilityIncidentTracker(self.runtime.memory)
                incident_id = tracker.record_incident(
                    incident_type="validation_failure",
                    description=f"STP Transition '{transition_name}' validation failed. Rolled back.",
                    metadata={
                        "transition_name": transition_name,
                        "integrity_issues": integrity_report.get("issues", []),
                    },
                )

            return {
                "success": False,
                "status": "validation_failed_rolled_back",
                "transition_name": transition_name,
                "incident_id": incident_id,
                "restored_snapshot": s0_snapshot_id,
                "integrity_report": integrity_report,
            }
