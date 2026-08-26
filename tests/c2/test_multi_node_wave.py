"""Tests for governed Multi-Node Big Jump Wave execution."""

from sage.c2.multi_node_wave import C2MultiNodeWaveEngine, NodeRole


def sample_nodes():
    def flights(prefix, namespace):
        return [
            *[{"flight_id": f"{prefix}_F{i}", "frontier_name": f"Frontier {i}", "target_namespaces": [f"{namespace}/{i}"], "is_reserve": False} for i in range(1, 6)],
            *[{"flight_id": f"{prefix}_R{i}", "frontier_name": f"Reserve {i}", "target_namespaces": [f"{namespace}/r{i}"], "is_reserve": True} for i in range(1, 3)],
        ]
    return {
        "NODE_A": {"role": NodeRole.PRIMARY_REPAIR.value, "flights": flights("A", "sage/a")},
        "NODE_B": {"role": NodeRole.INDEPENDENT_VERIFICATION.value, "flights": flights("B", "tests/b")},
        "NODE_C": {"role": NodeRole.ADVERSARIAL_RESEARCH.value, "flights": flights("C", "adversarial/c")},
    }


def test_three_node_wave_passes_with_15_active_and_6_reserve():
    receipt = C2MultiNodeWaveEngine().execute_multi_node_wave("TEST", sample_nodes())
    assert receipt.reconvergence_verdict == "PASS"
    assert receipt.flow_anti_drift_verified is True
    assert receipt.collision_check_passed is True
    assert receipt.total_flights_executed == 15
    assert receipt.total_reserve_slots_allocated == 6
    assert len(receipt.receipt_hash) == 64


def test_flow_alteration_fails_closed():
    receipt = C2MultiNodeWaveEngine().execute_multi_node_wave("TEST", sample_nodes(), attempted_flow_alteration=True)
    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.total_flights_executed == 0


def test_invalid_flight_count_fails_closed():
    nodes = sample_nodes()
    nodes["NODE_A"]["flights"] = nodes["NODE_A"]["flights"][1:]
    receipt = C2MultiNodeWaveEngine().execute_multi_node_wave("TEST", nodes)
    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.flow_anti_drift_verified is False


def test_namespace_collision_fails_closed():
    nodes = sample_nodes()
    nodes["NODE_B"]["flights"][0]["target_namespaces"] = ["sage/a/1"]
    receipt = C2MultiNodeWaveEngine().execute_multi_node_wave("TEST", nodes)
    assert receipt.reconvergence_verdict == "FAIL_CLOSED"
    assert receipt.collision_check_passed is False
