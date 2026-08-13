"""SAGE ACT-PROD Operator Dashboard.

Provides high-fidelity, operator-visible dashboards of SAGE session states,
archived trace lineages, and capability health.
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path

from sage.archive.core import Archive
from sage.capability_registry import SAGEOperationalCapabilityRegistry


class SAGEActProdDashboard:
    """ASCII dashboard rendering and analysis for enterprise operator visibility."""

    def __init__(
        self,
        archive_path: str = "sage_data/archive",
        registry_path: str = "evidence_capture/operational_capability_registry.json"
    ) -> None:
        self.archive = Archive(storage_path=archive_path)
        self.registry = SAGEOperationalCapabilityRegistry(storage_path=registry_path)

    def render_summary(self) -> str:
        """Render overall summary of all archived revalidation traces and status."""
        entries = self.archive.list_all()
        revalidation_entries = [e for e in entries if "revalidation" in e.tags]

        ascii_output = f"""
======================================================================
                 SAGE ACT-PROD ACTIVE WORKSPACE TRACES
======================================================================
Total Archived Entries:                 {len(entries)}
Total Revalidation Run Traces:          {len(revalidation_entries)}
----------------------------------------------------------------------
"""
        for entry in revalidation_entries:
            content = entry.content or {}
            actual_results = content.get("actual_results", {})
            progression = content.get("state_progression", {})
            telemetry = content.get("telemetry", {})
            status = "HEALTHY" if actual_results.get("success") else "BLOCKED"

            ascii_output += f"""Run ID: {entry.id}
  Receipt block:  {telemetry.get('evidence_receipt_id', 'UNKNOWN')}
  Duration:       {telemetry.get('duration_seconds', 0.0):.2f}s
  Status:         [{status}]
  Terminal state: {progression.get('terminal_state', 'UNKNOWN')}
----------------------------------------------------------------------
"""
        ascii_output += "======================================================================\n"
        return ascii_output

    def render_diagnostics(self) -> str:
        """Scans archived traces for corrupt, missing, or blocked entries."""
        entries = self.archive.list_all()
        stale_runs = []
        corrupt_runs = []

        # Check files on disk
        archive_dir = Path(self.archive.storage_path)
        if archive_dir.exists():
            for file in archive_dir.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception as e:
                    corrupt_runs.append({
                        "file": file.name,
                        "error": str(e)
                    })

        for e in entries:
            content = e.content or {}
            progression = content.get("state_progression", {})
            if progression.get("terminal_state") != "CLOSED":
                stale_runs.append(e.id)

        ascii_output = f"""
======================================================================
                 SAGE ACT-PROD DIAGNOSTICS & AUDIT
======================================================================
Stale/Unclosed Sessions:                {len(stale_runs)} {stale_runs}
Corrupted/Unreadable Files Detected:    {len(corrupt_runs)}
----------------------------------------------------------------------
"""
        for c in corrupt_runs:
            ascii_output += f"Corrupted file: {c['file']}\n  Error: {c['error']}\n"
        ascii_output += "======================================================================\n"
        return ascii_output

    def render_validation_scan(self) -> str:
        """Perform a complete scan of registered capabilities and validation statuses."""
        caps = self.registry.list_capabilities()

        ascii_output = """
======================================================================
                 SAGE CAPABILITY VALIDATION STATUS
======================================================================
"""
        for cap in caps:
            ascii_output += f"ID: {cap.capability_id:<30} | {cap.name:<30} | [{cap.validation_status}]\n"
        ascii_output += "======================================================================\n"
        return ascii_output
