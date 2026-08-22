"""Tests for deterministic frontier selection."""

from sage.capability_registry import SAGECapability
from sage.frontier_selection import rank_frontiers


def test_frontier_selection_prefers_high_value_incomplete_work():
    capabilities = [
        SAGECapability(capability_id="CAP-A", name="A", description="A", lifecycle_status="ACTIVE"),
        SAGECapability(
            capability_id="CAP-B", name="B", description="B",
            lifecycle_status="READY_FRONTIER", dependencies=["CAP-A"], incompletion_reason="Needs proof",
        ),
        SAGECapability(
            capability_id="CAP-C", name="C", description="C",
            lifecycle_status="PARTIAL", dependencies=["CAP-A", "CAP-B"],
        ),
    ]

    ranked = rank_frontiers(capabilities, limit=2)
    assert [cap_id for cap_id, _ in ranked] == ["CAP-B", "CAP-C"]
