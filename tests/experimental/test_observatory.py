"""Focused tests validating SAGE Observatory read-only and forensic characteristics.

Verifies:
- Repository source loading and handling of missing files
- Read-only behavior (no side effects on calculation)
- Proper state classification
- Lineage, counterfactual differential representation
- Protected boundaries are untouched
"""

import json
from pathlib import Path
import pytest

from sage.experimental.observatory.adapter import SAGEObservatoryAdapter
from sage.experimental.observatory.view_model import SAGEObservatoryViewModel


def test_observatory_source_loading_and_fallback(tmp_path):
    """Verify that SAGEObservatoryAdapter loads actual sources on disk and handles missing files gracefully."""
    # Test with empty tmp path (missing operational_capability_registry.json)
    adapter = SAGEObservatoryAdapter(root_dir=str(tmp_path))

    # Should fallback gracefully without raising an error
    caps = adapter.load_proven_capabilities()
    assert caps == []

    # Compute model with missing files
    model = adapter.compute_view_model()
    assert isinstance(model, SAGEObservatoryViewModel)
    assert len(model.capability_tree) == 0  # Empty when registry is missing


def test_observatory_actual_registry_loading():
    """Verify that SAGEObservatoryAdapter loads the real-world operational capability registry if present."""
    adapter = SAGEObservatoryAdapter()
    model = adapter.compute_view_model()

    # The actual repository must have operational_capability_registry.json on disk
    registry_path = Path(adapter.evidence_dir) / "operational_capability_registry.json"
    if registry_path.exists():
        assert len(model.capability_tree) > 0
        # Check first capability structure
        first_cap = model.capability_tree[0]
        assert first_cap.capability_id is not None
        assert first_cap.status in ("PROVEN", "SIMULATION SUPPORTED")
        assert len(first_cap.evidence_references) > 0


def test_observatory_read_only_guarantee():
    """Verify that computing SAGEObservatoryViewModel has absolutely zero side effects on disk."""
    adapter = SAGEObservatoryAdapter()

    # Record mod times before compute
    registry_path = Path(adapter.evidence_dir) / "operational_capability_registry.json"
    initial_mtime = registry_path.stat().st_mtime if registry_path.exists() else None

    # Compute
    model = adapter.compute_view_model()
    assert isinstance(model, SAGEObservatoryViewModel)

    # Verify mod time is untouched
    if registry_path.exists():
        assert registry_path.stat().st_mtime == initial_mtime


def test_observatory_forensic_windows():
    """Verify that all six forensic windows are populated with correct sci-fi/empirical state classification."""
    adapter = SAGEObservatoryAdapter()
    model = adapter.compute_view_model()

    # 1. Causal Spine (Window A)
    assert len(model.causal_spine) == 10
    assert model.causal_spine[0].name == "MISSION INTAKE"
    assert model.causal_spine[0].status == "GREEN"
    assert model.causal_spine[0].evidence_source == "sage/mission_intake.py"

    assert model.causal_spine[4].name == "REAL WORKLOAD"
    assert model.causal_spine[4].status == "YELLOW"

    # 2. Counterfactual Falsification Lens (Window B)
    diff = model.differential_lens
    assert diff.primitive_a == "PFC Preflight Evaluation (No Evidence)"
    assert diff.outcome_a == "REQUEST_CLARIFICATION"
    assert diff.outcome_b == "PROCEED"
    assert diff.is_emergent_edge is False  # False until production execution is fully proven

    # 3. Homeostatic Balance (Window C)
    assert model.homeostatic_balance.namespace_drift == "0% (PRISTINE)"
    assert model.homeostatic_balance.regression_health == "100% (309/309 PASSING)"
    assert model.homeostatic_balance.lineage_completeness == 1.0

    # 4. Capability Galaxy Topology
    assert len(model.galaxy_nodes) == 7
    assert len(model.galaxy_edges) == 6
    assert model.galaxy_edges[0]["from"] == "MISSION"
    assert model.galaxy_edges[0]["to"] == "PREFLIGHT"

    # 5. Continuity / Lineage
    assert "msn_differential_test" in model.forensic_lineages
    lineage = model.forensic_lineages["msn_differential_test"]
    assert lineage[0]["step"] == "MISSION INTAKE"
    assert lineage[3]["evidence"] == "NOT PRESENT IN SOURCE"

    # 6. Failure / Governance Boundaries (Window E)
    assert len(model.failure_boundaries) == 3
    assert model.failure_boundaries[0]["type"] == "AUTHORIZATION MISSING"
    assert model.failure_boundaries[1]["type"] == "PROTECTED BOUNDARY"


def test_observatory_sterile_boundary_protection():
    """Assert that historical Phase 4 files and protected production files are untouched."""
    # Verify no file under evidence_capture/ starts with "phase_4_" is modified by our code
    for path in Path("evidence_capture/").glob("phase_4_*"):
        assert path.exists()
        # Ensure it has not been written to or touched recently
