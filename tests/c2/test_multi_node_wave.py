"""
Unit and Integration Tests for C2 Multi-Node Big Jump Wave Execution Engine.
"""

import json
from pathlib import Path
import pytest

from sage.c2.multi_node_wave import (
    C2MultiNodeWaveEngine,
    FlightSpec,
    NodeRole,
)


@pytest.fixture
def wave_engine(tmp_path):
    return C2MultiNodeWaveEngine(repo_root=tmp_path)


def create_sample_nodes():
    return {
        "NODE_A": {
            "role": NodeRole.PRIMARY_REPAIR.value,
            "flights": [
                {
                    "flight_id": f"A_F{i}",
                    "frontier_name": f"Frontier A{i}",
                    "target_namespaces": [f"sage/module_a{i}/"],
                    "is_reserve": False,
                }
                for i in range(1, 6)
            ]
            + [
                {
                    "flight_id": f"A_R{i}",
                    "frontier_name": f"Reserve A{i}",
                    "target_namespaces": [f"sage/reserve_a{i}/"],
                    "is_reserve": True,
                }
                for i in range(1, 3)
            ],
        },
        "NODE_B": {
            "role": NodeRole.INDEPENDENT_VERIFICATION.value,
            "flights": [
                {
                    "flight_id": f"B_F{i}",
                    "frontier_name": f"Frontier B{i}",
                    "target_namespaces": [f"tests/module_b{i}/"],
                    "is_reserve": False,
                }
                for i in range(1, 6)
            ]
            + [
                {
                    "flight_id": f"B_R{i}",
                    "frontier_name": f"Reserve B{i}",
                    "target_namespaces": [f"tests/reserve_b{i}/"],
                    "is_reserve": True,
                }
                for i in range(1, 3)
            ],
        },
        "NODE_C": {
            "role": NodeRole.ADVERSARIAL_RESEARCH.value,
            "flights": [
                {
                    "flight_id": f"C_F{i}",
                    "frontier_name": f"Frontier C{i}",
                    "target_namespaces": [f"adversarial/module_c{i}/"],
                    "is_reserve": False,
                }
                for i in range(1, 6)
            ]
            + [
                {
                    "flight_id": f"C_R{i}",
                    "frontier_name": f"Reserve C{i}",
                    "target_namespaces": [f"adversarial/reserve_c{i}/"],
                    "is_reserve": True,
                }
                for i in range(1, 3)
            ],
        },
    }


def test_multi_node_wave_execution_success(wave_engine):
    nodes = create_sample_nodes()
    receipt = wave_engine.execute_multi_node_wave(
        wave_id="WAVE_TEST_001",
        nodes=nodes,
        attempted_flow_alteration=False,
    )

    assert receipt.reconvergence_verdict == "PASS"
    assert receipt.flow_anti_drift_verified is True
    assert receipt.collision_check_passed is True
    assert receipt.total_flights_executed == 15
    assert receipt.total_reserve_slots_allocated == 6
    assert len(receipt.receipt_hash) == 64
    assert len(receipt.node_results) == 3


def test_flow_anti_drift_fails_on_attempted_alteration(wave_engine):
    nodes = create_sample_nodes()
    receipt = wave_engine.execute_multi_node_wave(
        wave_id="WAVE_TEST_DRIFT_001",
        nodes=nodes,
        attempted_flow_alteration=True,
    )

    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.flow_anti_drift_verified is False
    assert receipt.total_flights_executed == 0


def test_flow_anti_drift_fails_on_invalid_flight_count(wave_engine):
    nodes = create_sample_nodes()
    # Remove one flight from Node A (making it 4 active flights instead of 5)
    nodes["NODE_A"]["flights"].pop(0)

    receipt = wave_engine.execute_multi_node_wave(
        wave_id="WAVE_TEST_INVALID_COUNT_001",
        nodes=nodes,
        attempted_flow_alteration=False,
    )

    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.flow_anti_drift_verified is False


def test_namespace_collision_detection_fails_closed(wave_engine):
    nodes = create_sample_nodes()
    # Introduce namespace collision between Node A and Node B
    nodes["NODE_B"]["flights"][0]["target_namespaces"] = ["sage/module_a1/"]

    receipt = wave_engine.execute_multi_node_wave(
        wave_id="WAVE_TEST_COLLISION_001",
        nodes=nodes,
        attempted_flow_alteration=False,
    )

    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.collision_check_passed is False


def test_protocol_document_exists():
    protocol_doc = Path(__file__).resolve().parent.parent.parent / "docs" / "governance" / "C2_MULTI_NODE_BIG_JUMP_WAVE_PROTOCOL.md"
    assert protocol_doc.exists()
    content = protocol_doc.read_text(encoding="utf-8")
    assert "C2_MULTI_NODE_BIG_JUMP_WAVE_PROTOCOL" in content
    assert "JULES NODE A" in content
    assert "JULES NODE B" in content
    assert "JULES NODE C" in content
    assert "Zero Flow Alteration" in content
