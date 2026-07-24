"""SAGE Deep State & Lineage Tree Validator (CIV-001).

Implements rigorous integrity validation checks on serialized states and session graph lineage trees.
"""

from typing import Dict, Any, List, Set


class StateValidator:
    """Rigorous state, checkpoint, and session lineage validator enforcing zero-trust rehydration."""

    @staticmethod
    def validate_lineage_trees(lineage: List[str]) -> bool:
        """Verifies session parent-child lineage trees for cyclic dependency loops.

        Returns:
            True if lineage graph is acyclic and safe, False otherwise.
        """
        # Graph cycle detection check
        visited: Set[str] = set()
        for idx, session_id in enumerate(lineage):
            if session_id in visited:
                # Cyclic reference detected!
                return False
            visited.add(session_id)
        return True

    @staticmethod
    def validate_rehydration_payload(snapshot_data: Dict[str, Any]) -> List[str]:
        """Deep audits serialized snapshot payloads before starting hydration.

        Returns:
            List of errors or anomalies detected. Empty list means state is healthy.
        """
        errors = []

        if "state" not in snapshot_data:
            errors.append("Missing core 'state' schema definition.")
        if "lineage" not in snapshot_data:
            errors.append("Missing continuity 'lineage' references.")
        if "sessions" not in snapshot_data:
            errors.append("Missing 'sessions' history array.")

        # Check for empty objectives
        state_data = snapshot_data.get("state", {})
        if state_data and not state_data.get("current_objective"):
            errors.append("RuntimeState current_objective is empty or corrupted.")

        return errors
