"""SAGE ACT-PROD Enterprise Cross-Model Audit & Recovery Dashboard.

Consumes actual persisted ArchiveEntry traces to provide real-time operator visibility
into SAGE mission states, execution lineage, evidence/receipt relationships, and
capability validation statuses.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from sage.archive.core import Archive
from sage.models import ArchiveEntry


class SAGEActProdDashboard:
    """Enterprise operator dashboard for SAGE execution, lineage, and audit traces."""

    def __init__(self, archive_path: str = "sage_data/archive") -> None:
        self.archive_path = Path(archive_path)
        self.archive = Archive(str(self.archive_path))

    def retrieve_operator_summary(self) -> Dict[str, Any]:
        """Compile a high-level summary of SAGE workspace revalidation metrics and statuses."""
        self.archive._load_all_entries()  # Ensure we have fresh entries loaded
        entries = self.archive.list_all()

        total_reval_missions = 0
        successful_missions = 0
        revalidated_capabilities_set = set()
        mission_list: List[Dict[str, Any]] = []

        for entry in entries:
            # Only summarize workspace revalidation entries
            if "revalidation" in entry.tags:
                total_reval_missions += 1
                content = entry.content or {}

                success = content.get("overall_success", False)
                if success:
                    successful_missions += 1

                reval_caps = content.get("revalidated_capabilities", [])
                for cap in reval_caps:
                    revalidated_capabilities_set.add(cap)

                # Lineage details
                source = "unknown"
                val_by = "unknown"
                if entry.intelligence and entry.intelligence.lineage:
                    source = entry.intelligence.lineage.source
                    if entry.intelligence.lineage.validation_record:
                        val_by = entry.intelligence.lineage.validation_record.validated_by

                mission_list.append({
                    "mission_id": content.get("mission_id", entry.id),
                    "success": success,
                    "final_state": content.get("final_state", "CLOSED"),
                    "source": source,
                    "validated_by": val_by,
                    "revalidated_capabilities": reval_caps
                })

        success_rate = (successful_missions / total_reval_missions * 100) if total_reval_missions > 0 else 0.0

        return {
            "total_archived_traces": len(entries),
            "revalidation_metrics": {
                "total_missions_evaluated": total_reval_missions,
                "successful_revalidations": successful_missions,
                "success_rate_percent": success_rate,
                "unique_capabilities_revalidated": list(revalidated_capabilities_set),
            },
            "active_missions": mission_list
        }

    def retrieve_mission_diagnostics(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Fetch deep diagnostic traces, stage-by-stage progressions, and workload logs for a mission."""
        archive_id = f"ARCHIVE-REVAL-{mission_id}"
        entry = self.archive.retrieve_entry(archive_id)
        if not entry:
            return None

        content = entry.content or {}

        # Parse validation record
        rules_applied: List[str] = []
        validated_by = "unknown"
        if entry.intelligence and entry.intelligence.lineage:
            if entry.intelligence.lineage.validation_record:
                rules_applied = entry.intelligence.lineage.validation_record.rules_applied
                validated_by = entry.intelligence.lineage.validation_record.validated_by

        # Extract sequence transitions
        transitions = content.get("transition_trace", [])
        transition_steps = [
            {
                "previous_state": t.get("previous_state"),
                "target_state": t.get("target_state"),
                "reason": t.get("decision_reason")
            }
            for t in transitions
        ]

        # Extract command executions
        exec_results = content.get("execution_results", [])
        workloads = [
            {
                "command": e.get("command_run"),
                "success": e.get("success"),
                "return_code": e.get("returncode")
            }
            for e in exec_results
        ]

        return {
            "mission_id": mission_id,
            "archive_entry_id": entry.id,
            "overall_success": content.get("overall_success", False),
            "final_state": content.get("final_state", "CLOSED"),
            "validated_by": validated_by,
            "rules_applied": rules_applied,
            "revalidated_capabilities": content.get("revalidated_capabilities", []),
            "transition_steps": transition_steps,
            "workload_executions": workloads
        }

    def handle_corrupted_archive_data(self) -> Dict[str, Any]:
        """Scan, identify, and gracefully isolate malformed or corrupted archive trace files."""
        corrupted_files = []
        if not self.archive_path.exists():
            return {"status": "ok", "corrupted_count": 0, "details": []}

        for filepath in self.archive_path.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Verify minimally required ArchiveEntry keys
                    for key in ["id", "title", "knowledge_state"]:
                        if key not in data:
                            raise KeyError(f"Missing required attribute: '{key}'")
            except Exception as e:
                corrupted_files.append({
                    "file_path": str(filepath),
                    "error": str(e)
                })

        return {
            "status": "warning" if corrupted_files else "ok",
            "corrupted_count": len(corrupted_files),
            "details": corrupted_files
        }
