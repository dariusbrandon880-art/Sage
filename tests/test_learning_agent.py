"""Unit and integration tests for the SAGE Governed Learning Agent (Phase 4.2)."""

import pytest
from sage.agents.models import AgentIdentity, PermissionBoundary, AgentRole, MemoryAccess, ValidationAuthority
from sage.agents.router import AgentTaskRouter
from sage.agents.learning import GovernedLearningAgent, PolicyProposal, PolicyProposalBridge
from sage.core.spek import SpekEngine


def test_unauthorized_learning_agents_rejected():
    """Prove that unauthorized or unregistered agents are strictly rejected from receiving observations or generating proposals."""
    # Create agent profile
    identity = AgentIdentity(
        agent_id="test_learner_123",
        name="Test Learner",
        role=AgentRole.CONTRIBUTOR,
        signature_key="learner_private_key_abc",
    )
    boundary = PermissionBoundary(agent_id="test_learner_123")
    agent = GovernedLearningAgent(identity, boundary)

    router = AgentTaskRouter()
    observations = {"system_load": 0.42, "authority_stability": 1.0}

    # Agent is not registered in router -> receive_observations should raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        agent.receive_observations(observations, router)
    assert "Unauthorized Agent Access" in str(exc_info.value)

    # Agent is not registered in router -> generate_policy_proposal should raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        agent.generate_policy_proposal(
            proposal_id="proposal_1",
            target_component="control_plane",
            proposed_setting="isolation_mode",
            value="strict",
            rationale="increase isolation on high load",
            observations=observations,
            router=router,
        )
    assert "Unauthorized Agent Access" in str(exc_info.value)


def test_valid_learning_proposal_generates_consistent_sha256_evidence():
    """Prove that authorized learning agents successfully process observations and generate consistent SHA-256 receipts."""
    identity = AgentIdentity(
        agent_id="authorized_learner",
        name="Secure Learner",
        role=AgentRole.CONTRIBUTOR,
        signature_key="secure_learning_key_999",
    )
    boundary = PermissionBoundary(agent_id="authorized_learner")
    agent = GovernedLearningAgent(identity, boundary)

    router = AgentTaskRouter()
    # Register the agent in the router to grant authorization
    router.register_agent(identity, boundary)

    observations = {"active_errors": 0, "telemetry_ping": "ok"}

    # 1. Receive observations and verify hash
    obs_hash = agent.receive_observations(observations, router)
    assert len(obs_hash) == 64  # Valid SHA-256 length

    # 2. Generate policy proposal
    proposal = agent.generate_policy_proposal(
        proposal_id="proposal_policy_002",
        target_component="cache_layer",
        proposed_setting="ttl",
        value=3600,
        rationale="optimize lookups based on telemetry ping success",
        observations=observations,
        router=router,
    )

    # 3. Assert proposal properties and SHA-256 consistency
    assert proposal.proposal_id == "proposal_policy_002"
    assert proposal.target_component == "cache_layer"
    assert proposal.proposed_setting == "ttl"
    assert proposal.value == 3600
    assert proposal.observations_hash == obs_hash
    assert len(proposal.evidence_signature) == 64

    # 4. Generate identical proposal and verify signature hash is exactly identical (determinism)
    bridge2 = PolicyProposalBridge()
    prop_raw = bridge2.generate_proposal(
        proposal_id="proposal_policy_002",
        target_component="cache_layer",
        proposed_setting="ttl",
        value=3600,
        rationale="optimize lookups based on telemetry ping success",
        observations=observations,
    )
    # Ensure they have identical timestamps for deterministic validation
    prop_raw.timestamp = proposal.timestamp

    sig2 = bridge2.generate_sha256_evidence_receipt(prop_raw, "secure_learning_key_999")
    assert proposal.evidence_signature == sig2


def test_sequential_evidence_receipt_chaining():
    """Verify that multiple proposals link sequentially in an evidence chain (previous_receipt_hash)."""
    identity = AgentIdentity(
        agent_id="authorized_learner",
        name="Secure Learner",
        role=AgentRole.CONTRIBUTOR,
        signature_key="secure_key",
    )
    boundary = PermissionBoundary(agent_id="authorized_learner")
    agent = GovernedLearningAgent(identity, boundary)

    router = AgentTaskRouter()
    router.register_agent(identity, boundary)

    obs1 = {"metric": "A"}
    obs2 = {"metric": "B"}

    # Generate proposal 1
    p1 = agent.generate_policy_proposal(
        "prop_1", "engine", "setting_a", 10, "rational 1", obs1, router
    )
    assert p1.previous_receipt_hash == "sage_learning_genesis_hash"

    # Generate proposal 2 - should link back to p1's evidence signature
    p2 = agent.generate_policy_proposal(
        "prop_2", "engine", "setting_b", 20, "rational 2", obs2, router
    )
    assert p2.previous_receipt_hash == p1.evidence_signature


def test_spek_validation_and_promotion_flow(tmp_path):
    """Verify integration with SPEK lifecycle engine and promotion candidates routing."""
    identity = AgentIdentity(
        agent_id="authorized_learner",
        name="Secure Learner",
        role=AgentRole.CONTRIBUTOR,
        signature_key="secure_key",
    )
    boundary = PermissionBoundary(agent_id="authorized_learner")
    agent = GovernedLearningAgent(identity, boundary)

    router = AgentTaskRouter()
    router.register_agent(identity, boundary)

    # Initialize a clean SPEK Engine
    spek_vault = tmp_path / "spek_vault.json"
    promotion_queue = tmp_path / "promotion_queue.log"
    negative_results = tmp_path / "negative_results.json"
    hdg_causality = tmp_path / "hdg_causality.json"

    spek = SpekEngine(
        vault_path=spek_vault,
        promotion_path=promotion_queue,
        rejection_path=negative_results,
        hdg_path=hdg_causality,
    )

    observations = {"authority_index": 1.0}
    proposal = agent.generate_policy_proposal(
        "policy_proposal_test",
        "boundary_enforcer",
        "auth_pacing",
        "active",
        "ensure strict pacing on audit",
        observations,
        router,
    )

    # Request SPEK validation/approval under system token
    spek_proposal = agent.request_spek_approval(proposal, spek, auth_token="SYSTEM_TOKEN")

    # Assert proposal reached APPROVED state (since score is 1.0 >= evidence_threshold)
    from sage.core.models import RuleState
    assert spek_proposal.state == RuleState.APPROVED


def test_runtime_contract_remains_unchanged():
    """Ensure the invariant sage.runtime.app == sage.api.app remains 100% active and identical."""
    import sage.runtime
    import sage.api
    assert getattr(sage.runtime, "app") is sage.api.app
