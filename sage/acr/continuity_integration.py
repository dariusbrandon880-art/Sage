"""Continuity Advancement Layer for SAGE 2.

Implements StateCalibrationSync, RecoveryWorkflow, and automated state reconciliation
and repair mechanisms across databases.
"""

import json
from typing import Any

from sage.acr.session import SessionState


class StateCalibrationSync:
    """Synchronizes, calibrates, and reconciles state drift across SAGE databases."""

    def __init__(self, runtime: Any):
        """Initialize State Calibration.

        Args:
            runtime: SAGERuntime process host.
        """
        self.runtime = runtime

    def calibrate_all(self) -> dict[str, Any]:
        """Examines state stores, calibrating and reconciling any detected drift.

        Returns:
            Dictionary detailing calibrated items and repaired links.
        """
        reconciled_items = []
        fixed_links_count = 0

        # 1. Calibrate active task context tracker alignment
        active_task = self.runtime.current_state.active_task
        context = self.runtime.context_tracker.get_current_context()
        if active_task and f"task:{active_task}" not in context.unresolved_items:
            context.unresolved_items.append(f"task:{active_task}")
            self.runtime.context_tracker.save_context()
            reconciled_items.append("active_task_context_alignment")

        # 2. Reconcile Decision Tracker evidence links pointing to archived memories
        all_decisions = self.runtime.decisions.list_all()
        for dec in all_decisions:
            new_evidence = []
            modified = False
            for ev_id in dec.evidence:
                # If evidence exists as promoted archive entry, replace with correct archive ID
                archive_id = f"archive_{ev_id}"
                if self.runtime.archive.retrieve_entry(archive_id):
                    new_evidence.append(archive_id)
                    modified = True
                    fixed_links_count += 1
                else:
                    new_evidence.append(ev_id)

            if modified:
                dec.evidence = new_evidence
                self.runtime.decisions._save_decision(dec)

        if fixed_links_count > 0:
            reconciled_items.append(f"reconciled_{fixed_links_count}_archived_decision_links")

        # 3. Synchronize Telemetry state calibration metrics
        from sage.runtime.metrics import get_metrics_collector

        metrics = get_metrics_collector()
        metrics.set_gauge("calibration.drift_reconciled", float(len(reconciled_items)))

        return {
            "status": "calibrated",
            "reconciled_keys": reconciled_items,
            "fixed_decision_links": fixed_links_count,
        }


class RecoveryWorkflow:
    """Manages system recovery, session repair, and workspace snapshot re-hydration."""

    def __init__(self, runtime: Any):
        """Initialize Recovery Workflow.

        Args:
            runtime: SAGERuntime process host.
        """
        self.runtime = runtime

    def repair_corrupted_sessions(self) -> int:
        """Scan session files and repair any missing or un-parseable session indices."""
        repaired_count = 0
        storage_path = self.runtime.session_manager.storage_path

        if not storage_path.exists():
            return 0

        # Scan for session files that might be corrupted or missing from the memory index
        for filepath in storage_path.glob("*.json"):
            session_id = filepath.stem
            if session_id not in self.runtime.session_manager.sessions:
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    state = SessionState(**data)
                    self.runtime.session_manager.sessions[session_id] = state
                    repaired_count += 1
                except Exception:  # noqa: BLE001
                    # If corrupted, reconstruct a bare minimum safe session state from current objective
                    obj = self.runtime.current_state.current_objective or "Recovery State"
                    state = self.runtime.session_manager.create_session(
                        session_id=session_id, active_objectives=[obj]
                    )
                    repaired_count += 1

        return repaired_count

    def recover_from_latest_snapshot(self) -> bool:
        """Find the latest snapshot checkpoint and restore all databases cleanly."""
        snapshots = self.runtime.list_workspace_snapshots()
        if not snapshots:
            return False

        # Sort chronologically by timestamp
        try:
            snapshots.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
            latest_id = snapshots[0]["id"]
            return self.runtime.restore_workspace_snapshot(latest_id)
        except Exception:  # noqa: BLE001
            return False
