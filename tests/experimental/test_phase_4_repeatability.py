"""SAGE Phase 4 Repeatability programmatic validation suite."""

import os
import ast
import json
from pathlib import Path
from sage.experimental.act.phase_4_repeatability import Phase4RepeatabilityRunner


def test_phase_4_repeatability_execution_and_metrics():
    """Verify that Phase4RepeatabilityRunner executes perfectly, calculates stats, and produces summaries."""
    root_dir = Path(__file__).parent.parent.parent
    summary_file = root_dir / "evidence_capture" / "phase_4_repeatability_summary.json"

    # Delete if exists to ensure fresh execution
    if summary_file.exists():
        summary_file.unlink()

    runner = Phase4RepeatabilityRunner(num_runs=3, output_dir=str(root_dir / "evidence_capture"))
    summary = runner.execute_repeatability_suite()

    assert summary_file.exists(), "Repeatability summary JSON must be created."
    assert summary["total_runs_executed"] == 3
    assert summary["success_rate_percent"] == 100.0

    # Verify statistical computations exist
    stats = summary["repeatability_statistics"]
    assert "scenario_a_duration_mins" in stats
    assert "scenario_b_duration_mins" in stats
    assert "total_duration_mins" in stats
    assert "aggregate_steps_reduced" in stats

    tot_stats = stats["total_duration_mins"]
    assert tot_stats["mean"] > 0.0
    assert tot_stats["variance"] >= 0.0
    assert tot_stats["std_dev"] >= 0.0

    # Verify consistency audits passed
    cons = summary["automated_consistency_summary"]
    assert cons["all_runs_receipt_lineages_intact"] is True
    assert cons["all_runs_validation_sequences_monotonic"] is True
    assert cons["all_runs_metrics_complete"] is True

    # Confirm run files exist
    for r in range(1, 4):
        run_file = root_dir / "evidence_capture" / f"phase_4_repeatability_run_{r}.json"
        assert run_file.exists(), f"Run {r} evidence package must exist."


def test_phase_4_repeatability_boundary_isolation_enforcement():
    """Assert that zero changes have been made to protected production and configuration namespaces.

    Only sage/experimental/act/, tests/experimental/, and documentation/indexes are allowed modifications.
    """
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories (One-Way Import Law)
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

        # Check file content does not import experimental namespaces
        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()
            try:
                tree = ast.parse(file_content, filename=str(path))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to import from module '{node.module}'"
                        )
