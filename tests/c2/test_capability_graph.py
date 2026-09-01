"""Unit tests for SAGE C2 Capability Graph Engine and Integration."""

from pathlib import Path
import pytest

from sage.c2.build_jump_wave import FlightMissionSpec
from sage.c2.capability_graph import (
    CapabilityCandidateMission,
    CapabilityExecutionStatus,
    CapabilityGraphDigest,
    CapabilityGraphEngine,
    CapabilityNode,
)
from sage.c2.frontier_intelligence_bridge import FrontierIntelligenceBridge
from sage.capability_registry import CapabilityDisposition, SAGEOperationalCapabilityRegistry


def test_capability_graph_node_digest():
    node = CapabilityNode(
        capability_id="sage.experimental.causality_auditor",
        name="Causality Auditor",
        source_path="sage/experimental/causality_auditor.py",
        status=CapabilityExecutionStatus.TESTED,
        test_paths=("tests/experimental/test_causality_auditor.py",),
        dependencies=("sage.core",),
        classes=("DecisionCausalityAuditor",),
        functions=("audit_causality",),
        description="Audits decision causality.",
    )
    digest1 = node.compute_digest()
    digest2 = node.compute_digest()

    assert isinstance(digest1, str)
    assert len(digest1) == 64
    assert digest1 == digest2


def test_capability_graph_discovery_and_ranking(tmp_path):
    engine = CapabilityGraphEngine(repo_root=Path("."))
    nodes = engine.discover_repository_capabilities()

    assert len(nodes) > 0
    assert "sage.c2.capability_graph" in nodes
    assert "sage.experimental.causality_auditor" in nodes

    digest = engine.get_digest()
    assert isinstance(digest, CapabilityGraphDigest)
    assert digest.total_nodes == len(nodes)
    assert digest.edges_count > 0
    assert len(digest.graph_sha256) == 64

    candidates = engine.rank_candidate_missions(limit=5)
    assert len(candidates) <= 5
    for cand in candidates:
        assert isinstance(cand, CapabilityCandidateMission)
        assert isinstance(cand.flight_spec, FlightMissionSpec)
        assert cand.capability_delta > 0.0


def test_operational_capability_registry_graph_sync(tmp_path):
    reg_path = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(reg_path))

    initial_count = len(registry.list_capabilities())
    assert initial_count == 7  # 7 default capabilities

    added = registry.sync_from_capability_graph(repo_root=".")
    assert added > 0

    updated_count = len(registry.list_capabilities())
    assert updated_count == initial_count + added


def test_frontier_intelligence_bridge_discover_and_build_missions():
    bridge = FrontierIntelligenceBridge()
    missions = bridge.discover_and_build_missions(limit=5)

    assert len(missions) == 5
    flight_ids = [m.flight_id for m in missions]
    assert flight_ids == ["F1", "F2", "F3", "F4", "F5"]

    for mission in missions:
        assert isinstance(mission, FlightMissionSpec)
        assert mission.frontier_name.startswith("FRONTIER-")
        assert mission.target_path.startswith("sage/experimental/")
