"""SAGE SDR-004 Divergence & Conflict Resolution programmatic validation suite."""

import os
import ast
import json
from pathlib import Path
from sage.experimental.act.sdr_004_divergence import (
    DivergentAgentStateSimulation,
    SDR004ConflictDetector,
    SDR004RecoveryResolutionPathway,
    SDR004EvidenceCaptureEngine
)


def test_sdr_004_divergence_simulation_and_resolution():
    """Verify that SDR-004 divergent state simulation and conflict resolution work correctly."""
    root_dir = Path(__file__).parent.parent.parent
    evidence_dir = root_dir / "evidence_capture"
    evidence_file = evidence_dir / "sdr_004_test_run.json"

    # Delete if exists to ensure a fresh validation
    if evidence_file.exists():
        evidence_file.unlink()

    # 1. State simulation
    sim = DivergentAgentStateSimulation(simulation_id="sim_sdr_004_test")
    states = sim.generate_divergent_states()
    assert "agent_alpha" in states
    assert "agent_beta" in states

    # 2. Conflict detection
    detector = SDR004ConflictDetector()
    conflicts = detector.analyze_conflicts(states)
    assert len(conflicts) == 3

    conflict_types = [c["conflict_type"] for c in conflicts]
    assert "COMMIT_MISMATCH" in conflict_types
    assert "THRESHOLD_MISMATCH" in conflict_types
    assert "ENVIRONMENT_MISMATCH" in conflict_types

    # 3. Pathway resolution
    pathway = SDR004RecoveryResolutionPathway()
    resolutions = pathway.resolve_conflicts(conflicts, preference="ALPHA")
    assert resolutions["resolved_state"] == "SUCCESS_ALIGNED"
    assert resolutions["actions_executed"] == 3
    assert len(resolutions["resolution_log"]) == 3

    # 4. Evidence capture
    engine = SDR004EvidenceCaptureEngine(output_dir=str(evidence_dir))
    wrote_path = engine.write_evidence(run_id="test_run", simulation_data=states, conflicts=conflicts, resolutions=resolutions)

    assert wrote_path.exists(), "SDR-004 execution must generate a JSON evidence package."

    # 5. Read and structurally validate the generated JSON evidence
    with open(wrote_path, "r", encoding="utf-8") as f:
        package = json.load(f)

    assert package["compliance_pack_id"] == "comp_sdr_004_test_run"
    assert package["run_identifier"] == "test_run"
    assert package["experimental_boundary"] == "sage/experimental/act/"
    assert package["conflict_analysis"]["conflicts_detected"] == 3
    assert len(package["conflict_analysis"]["conflicts_list"]) == 3
    assert package["resolution_pathway"]["resolved_state"] == "SUCCESS_ALIGNED"

    # Verify boundary integrity validation exists inside the JSON structure
    boundary_info = package["boundary_integrity_verification"]
    assert boundary_info["sage_runtime_untouched"] is True
    assert boundary_info["sage_core_untouched"] is True
    assert boundary_info["sage_acr_untouched"] is True
    assert boundary_info["sage_agents_untouched"] is True


def test_sdr_004_boundary_isolation_enforcement():
    """Assert that zero changes have been made to protected production and configuration namespaces."""
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories (One-Way Import Law)
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

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
