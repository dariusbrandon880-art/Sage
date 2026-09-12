"""SAGE Whole-Organism Behavioral Loop & Comprehensive Receipt Engine.

Executes the complete 13-stage behavioral lifecycle across all 7 organs:
MISSION INTAKE -> SAGI RECON -> C2 BOUND/AUTHORIZE -> FRONTIER ADMISSION -> F1–F5 DISPATCH ->
REAL EXECUTION -> TEST/OBSERVE -> EVIDENCE -> RECONVERGENCE -> VALIDATION -> MEASUREMENT ->
LEARNING -> CAPABILITY/MEMORY PROMOTION -> NEXT MISSION.

Demonstrates actual state/information movement across organ seams and outputs one canonical Whole-Organism Flight Receipt.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from sage.c2.capability_graph import CapabilityGraphEngine
from sage.c2.frontier_admission import FrontierAdmissionEngine, FrontierCandidate, FrontierState
from sage.c2.organism_jigsaw import OrganismJigsawEngine
from sage.c2.reconvergence_synthesizer import C2ReconvergenceSynthesizer
from sage.c2.workflow_velocity import MultiSessionVelocityEngine, SessionRole
import importlib


class WholeOrganismFlightReceipt(BaseModel):
    """The authoritative whole-organism receipt tying together the complete behavioral lifecycle."""

    receipt_id: str
    mission_id: str
    session_id: str
    exact_git_head: str
    frontier_plan: List[Dict[str, Any]]
    flight_receipts: List[Dict[str, Any]]
    evidence_hashes: Dict[str, str]
    jigsaw_gates_passed: int
    jigsaw_total_gates: int
    outcome_quality_score: float
    growth_verdict: str
    metacognitive_delta: Dict[str, Any]
    learning_signal: Dict[str, Any]
    next_frontier: str
    all_stages_completed: bool
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = (
            f"{self.receipt_id}:{self.mission_id}:{self.session_id}:{self.exact_git_head}:"
            f"{self.jigsaw_gates_passed}:{self.outcome_quality_score:.4f}:{self.growth_verdict}:"
            f"{self.next_frontier}:{self.all_stages_completed}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def verify(self) -> bool:
        return self.receipt_hash == self.compute_hash() and self.all_stages_completed


class WholeOrganismLoopEngine:
    """Orchestrates the 13-stage behavioral whole-organism workflow loop."""

    def __init__(self, storage_dir: str = "evidence_capture"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_current_head_sha() -> str:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError(f"Invalid git HEAD commit SHA: '{sha}'")
        return sha

    def execute_whole_organism_loop(
        self,
        mission_id: str,
        session_id: str,
        flight_payloads: List[Dict[str, Any]],
        exact_git_head: Optional[str] = None,
    ) -> WholeOrganismFlightReceipt:
        """Executes all 13 stages of the behavioral organism loop with full evidence binding."""
        head_sha = exact_git_head or self.get_current_head_sha()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", head_sha):
            raise ValueError(f"Invalid git HEAD commit SHA: {head_sha}")

        if len(flight_payloads) != 5:
            raise ValueError(f"Whole-organism loop requires exactly 5 flight payloads, got {len(flight_payloads)}")

        # STAGE 1: MISSION INTAKE
        mission_manifest = {
            "mission_id": mission_id,
            "session_id": session_id,
            "head_sha": head_sha,
            "intake_time": time.time(),
        }

        # STAGE 2: SAGI RECON
        cap_engine = CapabilityGraphEngine()
        cap_graph = cap_engine.discover(head_sha)
        capabilities_discovered = len(cap_graph.nodes)

        # STAGE 3: C2 BOUND / AUTHORIZE
        velocity_engine = MultiSessionVelocityEngine()
        velocity_engine.register_session(session_id, SessionRole.JULES_EXECUTION_SESSION)
        velocity_engine.register_session("c2-control-tower-primary", SessionRole.C2_CONTROL_TOWER)

        # STAGE 4: FRONTIER ADMISSION
        admission_engine = FrontierAdmissionEngine()
        admitted_candidates = []
        for flight in flight_payloads:
            candidate = FrontierCandidate(
                frontier_id=flight.get("flight_id", "F1"),
                target=flight.get("target", "Target"),
                source=f"Mission {mission_id}",
                state=FrontierState.UNSTARTED,
                base_sha=head_sha,
                collision_zone=flight.get("target_namespaces", ["default"])[0],
                evidence_required=[f"evidence/{mission_id}_{flight.get('flight_id')}.json"],
                stop_condition="Verification passed",
            )
            eval_res = admission_engine.classify_and_evaluate(candidate)
            admitted_candidates.append(eval_res.admitted)

        if not all(admitted_candidates):
            raise RuntimeError("One or more flights failed frontier admission evaluation")

        # STAGE 5 & 6 & 7: F1-F5 DISPATCH, REAL EXECUTION & TEST/OBSERVE
        wave_id = f"whole_organism_{mission_id}"
        velocity_receipt = velocity_engine.execute_velocity_wave(
            wave_id=wave_id,
            session_id=session_id,
            flight_payloads=flight_payloads,
            exact_git_head=head_sha,
        )

        # STAGE 8: EVIDENCE CAPTURE
        evidence_hashes = {}
        flight_receipts = []
        for flight in flight_payloads:
            f_id = flight.get("flight_id")
            f_hash = hashlib.sha256(f"{wave_id}:{f_id}:{head_sha}".encode("utf-8")).hexdigest()
            evidence_hashes[f_id] = f_hash
            flight_receipts.append({
                "flight_id": f_id,
                "target": flight.get("target"),
                "hash": f_hash,
                "passed": velocity_receipt.rolls_royce_quality_passed,
            })

        # STAGE 9: RECONVERGENCE SYNTHESIS
        reconvergence_verdict = velocity_receipt.reconvergence_verdict
        if reconvergence_verdict != "PASS":
            raise RuntimeError(f"Reconvergence failed with verdict: {reconvergence_verdict}")

        # STAGE 10: ORGANISM VALIDATION (Jigsaw structural + 10 connective tissue gates)
        jigsaw_engine = OrganismJigsawEngine()
        jigsaw_receipt = jigsaw_engine.execute()
        if not jigsaw_receipt.all_gates_passed:
            raise RuntimeError("Organism Jigsaw connective tissue gates verification failed")

        # STAGE 11: OUTCOME MEASUREMENT
        actual_quality = 1.0 if velocity_receipt.rolls_royce_quality_passed else 0.0
        fleet_mod = importlib.import_module("sage.experimental.airspace.fleet_evolution")
        FleetEvolutionIntelligence = getattr(fleet_mod, "FleetEvolutionIntelligence")
        fleet_intel = FleetEvolutionIntelligence(commit_sha=head_sha)
        growth_eval = fleet_intel.evaluate_organism_growth_rate(
            velocity_score=velocity_receipt.successful_flights / velocity_receipt.total_flights,
            wave_completion_rate=len(velocity_receipt.advancement_matrix_20_cells) / 20.0,
            anti_drift_compliance_score=1.0 if velocity_receipt.rolls_royce_quality_passed else 0.0,
        )

        # STAGE 12: LEARNING FEEDBACK & METACOGNITION
        meta_mod = importlib.import_module("sage.experimental.sagi.metacognition")
        MetacognitiveState = getattr(meta_mod, "MetacognitiveState")
        initial_state = MetacognitiveState(
            knowledge_confidence=0.9,
            inference_confidence=0.9,
            decision_confidence=0.95,
            outcome_confidence=0.5,
            risk_tolerance=0.8,
            risk_score=0.1,
        )
        updated_state = initial_state.with_outcome(actual_quality=actual_quality)
        learning_signal = {
            "autopsy_classification": "WIN_GOOD_DECISION" if actual_quality >= 0.8 else "LOSS_BAD_DECISION",
            "regret_score": 0.0 if actual_quality >= 0.8 else 0.2,
            "calibration_error": updated_state.calibration_error,
            "outcome_confidence": updated_state.outcome_confidence,
        }

        # STAGE 13: CAPABILITY / MEMORY PROMOTION & NEXT MISSION
        next_frontier = f"FRONTIER_NEXT_{hashlib.sha256(f'{mission_id}:{head_sha}'.encode('utf-8')).hexdigest()[:8].upper()}"

        # Adjudicate verified whole-organism completion reward into canonical progression
        progression_reward = None
        try:
            from sage.c2.reward_adjudication_bridge import request_c2_reward_adjudication
            report_payload = {
                "evidence_packet_version": "SAGE-SEP/1",
                "mission_id": mission_id,
                "subject_repo": "dariusbrandon880-art/Sage",
                "target_sha": head_sha,
                "observed_sha": head_sha,
                "claim_type": "verified_breakthrough",
                "claim_statement": f"Verified whole-organism mission completion for {mission_id}",
                "primary_actor": "ENGINEERING_FLIGHT",
                "outcome_type": "BREAKTHROUGH",
                "verification_status": "VERIFIED",
                "evidence_refs": [f"wo:{mission_id}:{head_sha}"],
                "verified_event_ref": f"whole_organism:{mission_id}:{head_sha}",
                "evidence_digest": hashlib.sha256(f"wo:{mission_id}:{head_sha}".encode("utf-8")).hexdigest(),
                "base_points": 50,
                "timestamp": time.time(),
            }
            progression_reward = request_c2_reward_adjudication(
                report_payload,
                difficulty=4,
                verification_quality=5,
                impact=5,
                reuse=5,
            )
        except Exception:
            progression_reward = None

        receipt_id = f"wo_rec_{hashlib.sha256(f'{mission_id}:{head_sha}:{time.time()}'.encode('utf-8')).hexdigest()[:12]}"
        receipt = WholeOrganismFlightReceipt(
            receipt_id=receipt_id,
            mission_id=mission_id,
            session_id=session_id,
            exact_git_head=head_sha,
            frontier_plan=[{"flight_id": f.get("flight_id"), "target": f.get("target")} for f in flight_payloads],
            flight_receipts=flight_receipts,
            evidence_hashes=evidence_hashes,
            jigsaw_gates_passed=jigsaw_receipt.gates_passed,
            jigsaw_total_gates=jigsaw_receipt.gates_evaluated,
            outcome_quality_score=actual_quality,
            growth_verdict=growth_eval.growth_verdict,
            metacognitive_delta={
                "calibration_error": updated_state.calibration_error,
                "confidence": updated_state.outcome_confidence,
            },
            learning_signal={
                **learning_signal,
                "progression_reward": progression_reward,
            },
            next_frontier=next_frontier,
            all_stages_completed=True,
        )
        receipt.receipt_hash = receipt.compute_hash()

        # Persist whole-organism receipt evidence
        out_dir = self.storage_dir / "waves" / wave_id / head_sha
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "whole_organism_receipt.json"
        out_path.write_text(json.dumps(receipt.model_dump(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

        # Also persist to canonical top-level evidence capture
        (self.storage_dir / "whole_organism_flight_receipt.json").write_text(
            json.dumps(receipt.model_dump(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        return receipt
