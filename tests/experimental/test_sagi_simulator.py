"""Test suite for SAGI Digital Twin Brain Core Simulator, Phase 2 Search Loop & Phase 3 Research Graph."""

import pytest
from sage.experimental.sagi.state import SAGIState
from sage.experimental.sagi.sagi import SAGICandidateGenerator, CandidateProposal
from sage.experimental.sagi.verifier import SAGIVerifier
from sage.experimental.sagi.controller import SAGIEvolutionController
from sage.experimental.sagi.search_loop import SAGISearchLoop, SAGISearchLoopReceipt
from sage.experimental.sagi.research_graph import SAGIResearchNode, SAGIResearchGraph, SAGIResearchGraphReceipt


def test_sagi_genesis_initialization():
    """Verify genesis Ω state initialization and immutable I(t0) anchor."""
    state = SAGIState.initialize_genesis(state_id="test_sagi_genesis")
    assert state.state_id == "test_sagi_genesis"
    assert state.cycle_index == 0
    assert state.temperature == 0.7
    assert state.mutation_radius == 0.1
    assert len(state.identity_anchor.initial_sha256) == 64
    assert len(state.current_hash) == 64


def test_sagi_candidate_generation():
    """Verify candidate proposal generation and parameter shift bounds."""
    state = SAGIState.initialize_genesis()
    generator = SAGICandidateGenerator(seed=123)
    cand = generator.generate_candidate(state, persona_label="test_agent")

    assert cand.parent_state_hash == state.current_hash
    assert cand.persona_label == "test_agent"
    assert len(cand.proposal_hash) == 64
    assert abs(cand.mutation_delta["parameter_shift"]) <= state.mutation_radius


def test_crpl_f1_metadata_non_influence():
    """CRPL-F1 Falsification Test: Tier 3 metadata cannot influence proposal hash."""
    state = SAGIState.initialize_genesis()
    generator = SAGICandidateGenerator(seed=456)

    cand1 = generator.generate_candidate(state, tier3_metadata={"priority": "LOW", "region": "US"})
    cand2 = generator.generate_candidate(state, tier3_metadata={"priority": "CRITICAL", "region": "EU", "extra": "data"})

    # Force identical semantic fields
    cand2.proposal_id = cand1.proposal_id
    cand2.mutation_delta = cand1.mutation_delta
    cand2.mutation_radius = cand1.mutation_radius
    cand2.temperature = cand1.temperature
    cand2.proposal_hash = cand2.compute_sha256()

    # Even though tier3_metadata differs, proposal_hash MUST be byte-for-byte identical
    assert cand1.proposal_hash == cand2.proposal_hash


def test_crpl_f2_persona_non_influence():
    """CRPL-F2 Falsification Test: Personas and labels cannot influence proposal hash."""
    state = SAGIState.initialize_genesis()
    generator = SAGICandidateGenerator(seed=789)

    cand1 = generator.generate_candidate(state, persona_label="persona_alpha")
    cand2 = generator.generate_candidate(state, persona_label="persona_omega")

    # Force identical semantic fields
    cand2.proposal_id = cand1.proposal_id
    cand2.mutation_delta = cand1.mutation_delta
    cand2.mutation_radius = cand1.mutation_radius
    cand2.temperature = cand1.temperature
    cand2.proposal_hash = cand2.compute_sha256()

    # Even though persona_label differs, proposal_hash MUST be byte-for-byte identical
    assert cand1.proposal_hash == cand2.proposal_hash


def test_sagi_verification_and_fail_closed():
    """Verify verifier identity invariant and spectral stability enforcement."""
    state = SAGIState.initialize_genesis()
    generator = SAGICandidateGenerator(seed=101)
    verifier = SAGIVerifier(max_spectral_shift=0.2)

    # Valid candidate
    cand_valid = generator.generate_candidate(state)
    res_valid = verifier.verify_proposal(state, cand_valid)
    assert res_valid.is_valid is True
    assert res_valid.status == "APPROVED"
    assert res_valid.crpl_f1_passed is True
    assert res_valid.crpl_f2_passed is True

    # Invalid candidate: Excessive parameter shift exceeding spectral stability
    cand_invalid = generator.generate_candidate(state)
    cand_invalid.mutation_delta["parameter_shift"] = 0.95
    res_invalid = verifier.verify_proposal(state, cand_invalid)
    assert res_invalid.is_valid is False
    assert res_invalid.status == "REJECTED"
    assert "SPECTRAL_STABILITY_VIOLATION" in res_invalid.decision_reasoning


def test_sagi_evolution_controller_and_receipts():
    """Verify evolution controller cycles, temperature adaptation, and receipt generation."""
    controller = SAGIEvolutionController()

    # Cycle 1: Successful
    rcpt1 = controller.execute_evolution_cycle(tier3_metadata={"meta": "test_1"})
    assert rcpt1.verification_status == "APPROVED"
    assert rcpt1.crpl_f1_passed is True
    assert rcpt1.crpl_f2_passed is True
    assert len(rcpt1.receipt_sha256) == 64
    assert controller.state.temperature < rcpt1.temperature_before  # Temperature cooled

    # Cycle 2: Forced Failure
    rcpt2 = controller.execute_evolution_cycle(force_fail_closed=True)
    assert rcpt2.verification_status == "REJECTED"
    assert controller.state.temperature > rcpt2.temperature_before  # Temperature warmed

    # Verify Learning Metrics (PHASE-1H)
    metrics = controller.compute_learning_metrics()
    assert metrics["total_cycles"] == 2.0
    assert metrics["successful_cycles"] == 1.0
    assert metrics["failed_cycles"] == 1.0
    assert metrics["success_rate"] == 0.5
    assert metrics["failure_memory_size"] == 1.0


def test_sagi_failure_memory_non_repetition():
    """Verify failure memory records rejected proposals and prevents exact repeat mutations."""
    state = SAGIState.initialize_genesis()
    generator = SAGICandidateGenerator(seed=202)

    cand = generator.generate_candidate(state)
    delta = cand.mutation_delta

    assert generator.is_known_failure(delta) is False
    generator.record_failure(cand, failure_reason="TEST_REJECTION")
    assert generator.is_known_failure(delta) is True


# --- SAGI PHASE 2 SEARCH LOOP TESTS ---


def test_sagi_search_loop_initialization():
    """Verify SAGI search loop initialization and identity anchor preservation."""
    search_loop = SAGISearchLoop()
    assert search_loop.controller.state.cycle_index == 0
    assert len(search_loop.controller.state.identity_anchor.initial_sha256) == 64
    assert search_loop.max_depth == 5


def test_sagi_search_loop_candidate_approval_path():
    """Verify candidate approval path through search loop and Guardian verification."""
    search_loop = SAGISearchLoop()
    rcpt = search_loop.run_search_cycle(cycle_id="search_cycle_01", candidates_per_cycle=3)

    assert rcpt.cycle_id == "search_cycle_01"
    assert rcpt.candidates_tested == 3
    assert rcpt.candidates_approved == 3
    assert rcpt.candidates_rejected == 0
    assert rcpt.guardian_checks_passed is True
    assert rcpt.research_only is True
    assert len(rcpt.receipt_sha256) == 64


def test_sagi_search_loop_candidate_rejection_path():
    """Verify candidate rejection path updates failure memory and search loop metrics."""
    search_loop = SAGISearchLoop()
    rcpt = search_loop.run_search_cycle(
        cycle_id="search_cycle_fail",
        candidates_per_cycle=3,
        inject_invalid_candidate=True
    )

    assert rcpt.candidates_tested == 3
    assert rcpt.candidates_approved == 2
    assert rcpt.candidates_rejected == 1
    assert rcpt.failure_memory_size == 1
    assert rcpt.guardian_checks_passed is True


def test_sagi_search_loop_guardian_bypass_prevention():
    """Verify that unverified candidates attempting Guardian bypass are rejected immediately."""
    search_loop = SAGISearchLoop()
    rcpt = search_loop.run_search_cycle(
        cycle_id="search_cycle_bypass",
        candidates_per_cycle=3,
        bypass_guardian_attempt=True
    )

    assert rcpt.candidates_tested == 0
    assert rcpt.candidates_approved == 0
    assert rcpt.candidates_rejected == 3
    assert rcpt.guardian_checks_passed is False


def test_sagi_search_loop_deterministic_cycle_behavior():
    """Verify that search loop cycles serialize deterministically and preserve identity anchor."""
    state1 = SAGIState.initialize_genesis("det_state_01")
    gen1 = SAGICandidateGenerator(seed=999)
    loop1 = SAGISearchLoop(controller=SAGIEvolutionController(initial_state=state1, generator=gen1))

    rcpt1 = loop1.run_search_cycle("cycle_det_1")
    assert len(rcpt1.receipt_sha256) == 64
    assert rcpt1.identity_anchor == state1.identity_anchor.initial_sha256


# --- SAGI PHASE 3 RESEARCH GRAPH TESTS ---


def test_sagi_research_graph_initialization():
    """Verify SAGI research graph initialization and empty state posture."""
    graph = SAGIResearchGraph(graph_id="test_graph_alpha")
    assert graph.graph_id == "test_graph_alpha"
    assert len(graph.nodes) == 0
    assert len(graph.cycles_indexed) == 0
    assert graph.expected_identity_anchor is None


def test_sagi_research_graph_ingest_search_receipt():
    """Verify converting a SAGISearchLoopReceipt into a SAGIResearchNode and emitting graph receipt."""
    search_loop = SAGISearchLoop()
    search_rcpt = search_loop.run_search_cycle(cycle_id="search_cycle_g1", candidates_per_cycle=2)

    graph = SAGIResearchGraph(graph_id="graph_search_ingest")
    node = graph.ingest_search_receipt(search_rcpt)

    assert node.cycle_id == "search_cycle_g1"
    assert node.identity_anchor == search_rcpt.identity_anchor
    assert node.guardian_result == "APPROVED"
    assert len(node.node_sha256) == 64
    assert len(graph.nodes) == 1
    assert "search_cycle_g1" in graph.cycles_indexed

    # Emit graph receipt
    graph_rcpt = graph.emit_graph_receipt()
    assert graph_rcpt.graph_id == "graph_search_ingest"
    assert graph_rcpt.nodes_added == 1
    assert graph_rcpt.cycles_indexed == 1
    assert graph_rcpt.identity_anchor == search_rcpt.identity_anchor
    assert len(graph_rcpt.receipt_sha256) == 64


def test_sagi_research_graph_ingest_evolution_receipt():
    """Verify converting SAGIEvolutionReceipt into research nodes and querying nodes."""
    controller = SAGIEvolutionController()
    identity_anchor = controller.state.identity_anchor.initial_sha256

    evo_rcpt_pass = controller.execute_evolution_cycle()
    evo_rcpt_fail = controller.execute_evolution_cycle(force_fail_closed=True)

    graph = SAGIResearchGraph(graph_id="graph_evo_ingest")
    node_pass = graph.ingest_evolution_receipt(evo_rcpt_pass, identity_anchor)
    node_fail = graph.ingest_evolution_receipt(evo_rcpt_fail, identity_anchor)

    assert len(graph.nodes) == 2
    assert node_pass.guardian_result == "APPROVED"
    assert node_fail.guardian_result == "REJECTED"

    # Query nodes
    approved_nodes = graph.query_nodes(guardian_result="APPROVED")
    assert len(approved_nodes) == 1
    assert approved_nodes[0].node_id == node_pass.node_id

    failure_nodes = graph.query_nodes(has_failures_only=True)
    assert len(failure_nodes) == 1
    assert failure_nodes[0].node_id == node_fail.node_id


def test_sagi_research_graph_identity_boundary_enforcement():
    """Verify that adding a research node with a mismatched identity anchor raises ValueError."""
    graph = SAGIResearchGraph(expected_identity_anchor="a" * 64)

    mismatched_node = SAGIResearchNode(
        node_id="node_mismatch_01",
        cycle_id="cycle_01",
        identity_anchor="b" * 64,
        candidate_signature="cand_sig_01",
        guardian_result="APPROVED"
    )

    with pytest.raises(ValueError, match="SAGI Identity Boundary Violation"):
        graph.add_node(mismatched_node)


def test_sagi_research_graph_checksum_and_receipt_determinism():
    """Verify deterministic graph SHA-256 computation and graph receipt output."""
    search_loop = SAGISearchLoop()
    search_rcpt1 = search_loop.run_search_cycle(cycle_id="cycle_det_a", candidates_per_cycle=2)

    graph = SAGIResearchGraph(graph_id="graph_det")
    graph.ingest_search_receipt(search_rcpt1)

    hash1 = graph.compute_graph_sha256()
    hash2 = graph.compute_graph_sha256()

    assert len(hash1) == 64
    assert hash1 == hash2


# --- SAGI MEMORY TRUST & PROVENANCE ADVERSARIAL TESTS ---


def test_sagi_memory_poisoning_untrusted_node_rejection():
    """Adversarial Test: Untrusted nodes with forged or mismatched identity anchors are rejected."""
    valid_anchor = "c" * 64
    graph = SAGIResearchGraph(graph_id="trusted_graph", expected_identity_anchor=valid_anchor)

    forged_node = SAGIResearchNode(
        node_id="poison_node_01",
        cycle_id="cycle_poison",
        identity_anchor="f" * 64,  # Forged/Mismatched anchor
        candidate_signature="poison_sig",
        guardian_result="APPROVED",
    )

    with pytest.raises(ValueError, match="SAGI Identity Boundary Violation"):
        graph.add_node(forged_node)


def test_sagi_provenance_survives_cross_session_restart():
    """Verify provenance fields, hashes, and verification status survive serialization and restart."""
    search_loop = SAGISearchLoop()
    rcpt = search_loop.run_search_cycle(cycle_id="session_a_cycle", candidates_per_cycle=2)

    graph_a = SAGIResearchGraph(graph_id="session_a_graph")
    node_a = graph_a.ingest_search_receipt(rcpt)

    # Serialize node to dict/json (simulating disk persistence)
    node_serialized = node_a.model_dump()

    # Session B: Reconstruct node in fresh process context
    node_b = SAGIResearchNode(**node_serialized)

    assert node_b.node_id == node_a.node_id
    assert node_b.cycle_id == node_a.cycle_id
    assert node_b.identity_anchor == node_a.identity_anchor
    assert node_b.guardian_result == node_a.guardian_result
    assert node_b.node_sha256 == node_a.node_sha256
    assert node_b.timestamp == node_a.timestamp


def test_sagi_unverified_memory_cannot_bypass_governance():
    """Verify rejected/unverified research nodes cannot masquerade as approved knowledge."""
    search_loop = SAGISearchLoop()
    failed_rcpt = search_loop.run_search_cycle(
        cycle_id="failed_cycle",
        candidates_per_cycle=3,
        bypass_guardian_attempt=True,  # Forced rejection
    )

    graph = SAGIResearchGraph(graph_id="gov_test_graph")
    node = graph.ingest_search_receipt(failed_rcpt)

    assert node.guardian_result == "REJECTED"
    assert node.failure_state is not None

    # Querying approved nodes MUST exclude rejected nodes
    approved = graph.query_nodes(guardian_result="APPROVED")
    assert len(approved) == 0

    # The rejected node exists only as a recorded failure pattern
    failures = graph.query_nodes(has_failures_only=True)
    assert len(failures) == 1
    assert failures[0].node_id == node.node_id


def test_sagi_fact_vs_derived_knowledge_distinction():
    """Verify raw search observations and derived evolution receipts produce distinct, deterministic graph checksums."""
    search_loop = SAGISearchLoop()
    search_rcpt = search_loop.run_search_cycle("cycle_fact_01")

    controller = SAGIEvolutionController()
    evo_rcpt = controller.execute_evolution_cycle()

    graph = SAGIResearchGraph(graph_id="knowledge_graph")

    # Phase 1: Ingest raw search observation
    node_obs = graph.ingest_search_receipt(search_rcpt)
    checksum_obs = graph.compute_graph_sha256()

    # Phase 2: Ingest derived evolution receipt
    node_evo = graph.ingest_evolution_receipt(evo_rcpt, identity_anchor=search_rcpt.identity_anchor)
    checksum_evo = graph.compute_graph_sha256()

    assert checksum_obs != checksum_evo
    assert node_obs.candidate_signature != node_evo.candidate_signature
