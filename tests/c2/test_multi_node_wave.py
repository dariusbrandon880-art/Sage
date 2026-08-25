"""Unit tests for C2 Multi-Node Wave Engine & Lifecycle Matrix Binding."""

from sage.c2.multi_node_wave import C2MultiNodeWaveEngine, NodeExecutionSlot
from sage.c2.reconvergence_synthesizer import (
    LifecycleMilestoneRecord,
    LifecycleStage,
)

VALID_SHA = "db2592167dba5eda4c024bba9202ff085d9c1d9b"


def test_multi_node_wave_engine_synthesis():
    engine = C2MultiNodeWaveEngine(wave_id="multi-node-wave-001")

    nodes = ["Node-A", "Node-B", "Node-C", "Node-A", "Node-B"]
    for idx, node in enumerate(nodes, start=1):
        milestones = [
            LifecycleMilestoneRecord(stage=LifecycleStage.INTAKE_RECON, passed=True, evidence_ref=f"{node}_1"),
            LifecycleMilestoneRecord(stage=LifecycleStage.BOUNDED_BUILD, passed=True, evidence_ref=f"{node}_2"),
            LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=True, evidence_ref=f"{node}_3"),
            LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=True, evidence_ref=f"{node}_4"),
        ]
        slot = NodeExecutionSlot(
            node_id=node,
            flight_id=f"F{idx}",
            target=f"target_{idx}",
            exact_head=VALID_SHA,
            milestones=milestones,
        )
        engine.register_node_slot(slot)

    pkg = engine.reconverge_multi_node_wave()

    assert pkg.wave_id == "multi-node-wave-001"
    assert pkg.total_flights == 5
    assert pkg.successful_flights == 5
    assert pkg.reconvergence_verdict == "PASS"
    assert len(pkg.advancement_matrix_20_cells) == 20
    assert all(pkg.advancement_matrix_20_cells.values())
