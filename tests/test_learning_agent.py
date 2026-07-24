"""Validation tests for Phase 4.2 SAGE Learning Runtime Activation."""

import json
import hashlib
import pytest
from typing import Dict, Any

from sage.agents.learning.policy_bridge import AgentPolicyBridge
from sage.agents.learning.learning_agent import SAGELearningAgent


def test_unauthorized_agent_rejection():
    """Test 1: Unauthorized agent proposals are rejected by SPEK Policy Bridge."""
    bridge = AgentPolicyBridge(authorized_agents={"AUTHORIZED_AGENT"})

    receipt = bridge.evaluate_proposal(
        agent_id="UNAUTHORIZED_HACKER_AGENT",
        proposed_delta={"target": "learning_rate", "current_value": 0.01, "proposed_value": 0.005},
        evidence_metadata={"performance_improvement": 12.5}
    )

    assert receipt["status"] == "REJECTED"
    assert receipt["agent_id"] == "UNAUTHORIZED_HACKER_AGENT"


def test_valid_evidence_receipt_generation():
    """Test 2: Authorized agents generate valid evidence receipts."""
    bridge = AgentPolicyBridge(authorized_agents={"AUTHORIZED_AGENT"})

    # Case A: Standard automatic authorization
    receipt_auto = bridge.evaluate_proposal(
        agent_id="AUTHORIZED_AGENT",
        proposed_delta={"target": "learning_rate", "current_value": 0.01, "proposed_value": 0.005},
        evidence_metadata={"performance_improvement": 12.5}
    )
    assert receipt_auto["status"] == "AUTHORIZED"
    assert receipt_auto["agent_id"] == "AUTHORIZED_AGENT"
    assert "proposal_hash" in receipt_auto
    assert "timestamp" in receipt_auto
    assert receipt_auto["spek_version"] == "1.1"

    # Case B: Proposal requiring a manual gate (pending validation)
    receipt_pending = bridge.evaluate_proposal(
        agent_id="AUTHORIZED_AGENT",
        proposed_delta={"target": "learning_rate", "current_value": 0.01, "proposed_value": 0.005},
        evidence_metadata={"requires_manual_gate": True}
    )
    assert receipt_pending["status"] == "PENDING_VALIDATION"


def test_sha256_consistency_verification():
    """Test 3: SHA-256 consistency verification of proposed deltas."""
    bridge = AgentPolicyBridge(authorized_agents={"AUTHORIZED_AGENT"})
    proposed_delta = {"target": "decay_factor", "current_value": 0.95, "proposed_value": 0.9}

    receipt = bridge.evaluate_proposal(
        agent_id="AUTHORIZED_AGENT",
        proposed_delta=proposed_delta,
        evidence_metadata={"performance_improvement": 5.0}
    )

    # Re-calculate hash independently
    serialized_delta = json.dumps(proposed_delta, sort_keys=True)
    expected_hash = hashlib.sha256(serialized_delta.encode("utf-8")).hexdigest()

    assert receipt["proposal_hash"] == expected_hash


def test_runtime_contract_preservation():
    """Test 4: Runtime contract is preserved (sage.runtime.app == sage.api.app)."""
    from sage.runtime import app as runtime_app
    from sage.api import app as api_app

    assert runtime_app is not None
    assert runtime_app == api_app


def test_no_mutation_of_production_configuration():
    """Test 5: Bounded learning agents cannot directly modify or propose direct system file mutations."""
    bridge = AgentPolicyBridge()
    agent = SAGELearningAgent(agent_id="SAGE_LEARNING_AGENT_001", policy_bridge=bridge)

    # Observing a runtime event is successful and doesn't mutate config on disk
    agent.observe_runtime_event({"event_type": "telemetry", "metric": "cpu_utilization", "value": 15.4})
    assert len(agent.observed_events) == 1

    # Normal proposal should succeed
    res = agent.propose_improvement(
        target="max_concurrency",
        current_value=10,
        proposed_value=20,
        evidence={"sample_size": 100}
    )
    assert res["receipt"]["status"] == "AUTHORIZED"

    # Proposal with forbidden disk/system path changes must raise a PermissionError (fail-closed boundary)
    with pytest.raises(PermissionError) as exc_info:
        agent.propose_improvement(
            target="config",
            current_value="old_config",
            proposed_value={"config_file_path": "/etc/sage.conf"},
            evidence={"tamper_attempt": True}
        )
    assert "Security Boundary Violation" in str(exc_info.value)
