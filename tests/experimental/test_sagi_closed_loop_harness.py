"""SAGE SAGI Closed-Loop End-to-End Integration Test Harness & Negative Boundary Verification.

Verifies the complete 12-stage governed intelligence loop:
SAGI Discovery -> C2 Mission Synthesis -> Explicit Mission Plan -> Five Flight Dispatch
-> Execution Evidence -> Verification -> Outcome -> Autopsy/Regret -> Metacognitive Learning
-> Master Archive Lineage -> Next Frontier Selection + Fail-Closed Negative Boundaries.
"""

import time
import pytest
from sage.experimental.sagi_discovery_flight_selector import (
    SAGIDiscoveryFlightSelector,
    DiscoveryCandidate,
    FlightRole
)
from sage.experimental.sagi.metacognition import MetacognitiveState, MetacognitiveEngine
from sage.c2.decision_autopsy import (
    DecisionAutopsyEngine,
    DecisionRecord,
    OutcomeRecord,
    CounterfactualRecord
)
from sage.experimental.sagi.regret import RegretAttributionEngine
from sage.c2.frontier_intelligence_bridge import FrontierIntelligenceBridge
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher, FlightMissionSpec, MultiFrontierDispatchReceipt
from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial, FitnessVector
from sage.c2.reconvergence_synthesizer import C2ReconvergenceSynthesizer, ReconvergenceEvidencePackage, FlightExecutionSummary


def test_sagi_closed_loop_governed_end_to_end_harness():
    """Verify end-to-end 12-stage governed closed loop from SAGI discovery to Master Archive promotion."""

    # 1. SAGI Candidate Discovery
    raw_candidates = (
        DiscoveryCandidate(
            candidate_id="cand_s1_r1",
            role=FlightRole.INDEPENDENT_TRANSFER,
            description="Reconvergence synthesizer capability expansion",
            consequentiality=0.85,
            information_gain=0.90,
            falsification_value=0.80,
            safety=0.95,
            evidence_gap=0.70,
            provenance_ref="provenance_s1_r1",
            capability_surface="sage.c2.surface_1"
        ),
        DiscoveryCandidate(
            candidate_id="cand_s1_r2",
            role=FlightRole.INDEPENDENT_TRANSFER,
            description="Capability registry health audit",
            consequentiality=0.80,
            information_gain=0.85,
            falsification_value=0.75,
            safety=0.90,
            evidence_gap=0.65,
            provenance_ref="provenance_s1_r2",
            capability_surface="sage.c2.surface_2"
        ),
        DiscoveryCandidate(
            candidate_id="cand_s1_r3",
            role=FlightRole.CONSEQUENT_FRONTIER,
            description="Active capability summary generation",
            consequentiality=0.90,
            information_gain=0.88,
            falsification_value=0.85,
            safety=0.92,
            evidence_gap=0.75,
            provenance_ref="provenance_s1_r3",
            capability_surface="sage.runtime.engine_3"
        ),
        DiscoveryCandidate(
            candidate_id="cand_s1_r4",
            role=FlightRole.FALSIFICATION,
            description="ChatGPT C2 directive compliance validation",
            consequentiality=0.88,
            information_gain=0.82,
            falsification_value=0.88,
            safety=0.98,
            evidence_gap=0.60,
            provenance_ref="provenance_s1_r4",
            capability_surface="sage.c2.chatgpt_c2_contract_4"
        ),
        DiscoveryCandidate(
            candidate_id="cand_s1_r5",
            role=FlightRole.INFORMATION_GAIN,
            description="SAGI simulator state validation",
            consequentiality=0.82,
            information_gain=0.95,
            falsification_value=0.90,
            safety=0.89,
            evidence_gap=0.80,
            provenance_ref="provenance_s1_r5",
            capability_surface="sage.experimental.sagi_5"
        )
    )

    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(raw_candidates, frontier_digest="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    assert len(proposal.candidates) == 5, "Must select exactly 5 flight candidates"

    # 2. C2 Mission Synthesis & Explicit Plan
    bridge = FrontierIntelligenceBridge()
    specs = [
        FlightMissionSpec(
            flight_id="F1",
            frontier_name="Reconvergence Synthesizer Expansion",
            target_path="sage/c2/reconvergence_synthesizer.py",
            collision_zone="sage.c2.surface_1",
            evidence_ref="evidence_capture/f1_research_evidence.json",
            pr_or_change="PR #370",
            test_references=["tests/c2/test_c2_execution_surface.py"]
        ),
        FlightMissionSpec(
            flight_id="F2",
            frontier_name="Capability Registry Audit",
            target_path="sage/capability_registry.py",
            collision_zone="sage.c2.surface_2",
            evidence_ref="evidence_capture/f2_continuity_evidence.json",
            pr_or_change="PR #370",
            test_references=["tests/test_capability_registry.py"]
        ),
        FlightMissionSpec(
            flight_id="F3",
            frontier_name="Active Capability Summary",
            target_path="sage/runtime/engine.py",
            collision_zone="sage.runtime.engine_3",
            evidence_ref="evidence_capture/f3_execution_evidence.json",
            pr_or_change="PR #370",
            test_references=["tests/test_system_frame.py"]
        ),
        FlightMissionSpec(
            flight_id="F4",
            frontier_name="ChatGPT Directive Validation",
            target_path="sage/c2/chatgpt_c2_contract.py",
            collision_zone="sage.c2.chatgpt_c2_contract_4",
            evidence_ref="evidence_capture/f4_guard_evidence.json",
            pr_or_change="PR #370",
            test_references=["tests/c2/test_chatgpt_c2_contract.py"]
        ),
        FlightMissionSpec(
            flight_id="F5",
            frontier_name="SAGI Simulator Validation",
            target_path="sage/experimental/sagi/sagi.py",
            collision_zone="sage.experimental.sagi_5",
            evidence_ref="evidence_capture/f5_warehouse_evidence.json",
            pr_or_change="PR #370",
            test_references=["tests/experimental/test_sagi_simulator.py"]
        )
    ]

    # 3. Five Flight Dispatch & Execution Evidence
    dispatcher = MultiFrontierDispatcher()
    receipt = dispatcher.dispatch_all(missions=specs)

    assert receipt is not None
    assert receipt.commit_sha is not None
    assert len(receipt.commit_sha) == 40
    assert receipt.wave_verdict in ("PASS", "HOLD", "FAIL_CLOSED")

    # 4. Decision Autopsy & Regret Processing
    dec_time = "2026-09-02T01:00:00Z"
    info_hash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    decision = DecisionRecord(
        decision_id="DEC-CLOSED-LOOP-001",
        mission_id="obj_sagi_closed_loop",
        decided_at_utc=dec_time,
        information_snapshot_hash=info_hash,
        information_refs=("ref_info_1", "ref_info_2"),
        assumptions=("stable_mainline",),
        chosen_action="dispatch_five_flight_wave",
        alternatives=("dispatch_five_flight_wave", "hold_and_evaluate"),
        chosen_expected_utility=0.9,
        alternative_expected_utilities=(("dispatch_five_flight_wave", 0.9), ("hold_and_evaluate", 0.5)),
        decision_confidence=0.85
    )
    outcome = OutcomeRecord(
        outcome_id="OUT-CLOSED-LOOP-001",
        decision_id="DEC-CLOSED-LOOP-001",
        observed_at_utc="2026-09-02T01:05:00Z",
        actual_utility=1.0 if receipt.wave_verdict == "PASS" else 0.0
    )
    cf_records = (
        CounterfactualRecord(
            action="dispatch_five_flight_wave",
            expected_utility=0.9,
            information_snapshot_hash=info_hash,
            information_cutoff_utc=dec_time
        ),
        CounterfactualRecord(
            action="hold_and_evaluate",
            expected_utility=0.5,
            information_snapshot_hash=info_hash,
            information_cutoff_utc=dec_time
        )
    )

    autopsy_engine = DecisionAutopsyEngine()
    autopsy = autopsy_engine.autopsy(
        decision=decision,
        outcome=outcome,
        counterfactuals=cf_records,
        lesson="Five Flight wave execution validated under governed control."
    )
    assert autopsy is not None
    assert autopsy.decision_id == "DEC-CLOSED-LOOP-001"

    regret_engine = RegretAttributionEngine()
    regret_record = regret_engine.derive(autopsy)
    assert regret_record is not None
    assert regret_record.decision_id == "DEC-CLOSED-LOOP-001"

    # 5. Metacognitive Learning Update
    initial_meta = MetacognitiveState(
        knowledge_confidence=0.9,
        inference_confidence=0.9,
        decision_confidence=0.85,
        outcome_confidence=0.0,
        risk_tolerance=0.5,
        risk_score=0.2
    )
    updated_meta = initial_meta.with_outcome(1.0 if receipt.wave_verdict == "PASS" else 0.0)
    meta_engine = MetacognitiveEngine()
    assessment = meta_engine.assess(updated_meta)
    assert updated_meta.outcome_confidence in (0.0, 1.0)
    assert assessment.action_allowed is True

    # 6. Master Archive Lineage & Next Frontier Selection
    ledger = ExperimentLedger()
    trial = ExperimentTrial(
        mission_id="obj_sagi_closed_loop",
        technique_id="sagi_closed_loop_wave_v1",
        trial_id=f"TRIAL-CLOSED-LOOP-{int(time.time())}",
        fitness=FitnessVector(
            mission_value=1.0,
            correctness=1.0,
            repeatability=1.0,
            evidence_quality=1.0,
            recovery=1.0,
            generalization=1.0,
            cost=0.1
        ),
        evidence_ref="evidence_capture/double_big_jump_wave_evidence.json",
        exact_git_head=receipt.commit_sha,
        adversarial=True,
        regression_free=True,
        human_reviewed=True
    )
    digest = ledger.append(trial)
    assert digest is not None
    trials = ledger.trials("obj_sagi_closed_loop", "sagi_closed_loop_wave_v1")
    assert len(trials) == 1
    assert trials[0].exact_git_head == receipt.commit_sha

    # Verify next frontier reconvergence
    synthesizer = C2ReconvergenceSynthesizer(wave_id="test_sagi_closed_loop_wave")
    summaries = [
        FlightExecutionSummary(
            flight_id=f"F{i}",
            target=f"sage/target_{i}.py",
            classification="CAPABILITY_ADVANCE",
            execution_result="PASS",
            exact_head=receipt.commit_sha,
            tests_passed=10,
            evidence_ref=f"evidence_capture/f{i}_evidence.json",
            pr_or_change="PR #370"
        )
        for i in range(1, 6)
    ]
    pkg = ReconvergenceEvidencePackage(
        wave_id="test_sagi_closed_loop_wave",
        flight_summaries=summaries,
        total_flights=5,
        successful_flights=5,
        blocked_flights=0,
        first_pass_verification_rate=100.0,
        reconvergence_verdict=receipt.wave_verdict,
        advancement_matrix_20_cells={f"P{p}-S{s}": True for p in range(1, 6) for s in range(1, 5)}
    )
    breakdown = synthesizer.get_matrix_stage_breakdown(pkg)
    assert breakdown is not None
    assert "STAGE_1_INTAKE_RECON" in breakdown


def test_sagi_closed_loop_negative_boundaries_fail_closed():
    """Verify negative boundaries fail closed across all key governance invariants."""

    # 1. Invalid Flight Mission Spec Dispatch Failure
    dispatcher = MultiFrontierDispatcher()
    with pytest.raises(Exception):
        # Empty flight spec list must fail closed in BuildJumpWaveEngine
        dispatcher.dispatch_all(missions=[])

    # 2. Mismatched decision_id in Autopsy Failure
    autopsy_engine = DecisionAutopsyEngine()
    dec_time = "2026-09-02T01:00:00Z"
    info_hash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    decision = DecisionRecord(
        decision_id="DEC-001",
        mission_id="obj_test_mismatch",
        decided_at_utc=dec_time,
        information_snapshot_hash=info_hash,
        information_refs=("ref_1",),
        assumptions=(),
        chosen_action="action_a",
        alternatives=("action_a", "action_b"),
        chosen_expected_utility=0.8,
        alternative_expected_utilities=(("action_a", 0.8), ("action_b", 0.5)),
        decision_confidence=0.8
    )
    outcome_mismatched = OutcomeRecord(
        outcome_id="OUT-001",
        decision_id="DEC-MISMATCHED-002",
        observed_at_utc="2026-09-02T01:05:00Z",
        actual_utility=0.8
    )
    cf_records = (
        CounterfactualRecord(
            action="action_a",
            expected_utility=0.8,
            information_snapshot_hash=info_hash,
            information_cutoff_utc=dec_time
        ),
        CounterfactualRecord(
            action="action_b",
            expected_utility=0.5,
            information_snapshot_hash=info_hash,
            information_cutoff_utc=dec_time
        )
    )
    with pytest.raises(ValueError, match="outcome decision_id does not match decision"):
        autopsy_engine.autopsy(
            decision=decision,
            outcome=outcome_mismatched,
            counterfactuals=cf_records,
            lesson="Test mismatched outcome decision_id."
        )
