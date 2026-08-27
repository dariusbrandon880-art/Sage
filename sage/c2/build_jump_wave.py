"""SAGE Big Jump Wave Engine with identity-addressed execution evidence."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from sage.c2.flight_collision_lock import FlightCollisionLockManager, FlightLockRequest
from sage.c2.flight_gps.engine import FlightGPS
from sage.c2.flight_gps.models import FlightLifecycle, FlightManifest, OwnershipFingerprint
from sage.c2.frontier_admission import FrontierAdmissionEngine, FrontierCandidate, FrontierState
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
    ReconvergenceEvidencePackage,
)


class FlightMissionSpec(BaseModel):
    flight_id: str
    frontier_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: List[str] = Field(default_factory=list)


CANONICAL_BIG_JUMP_MISSIONS: List[FlightMissionSpec] = [
    FlightMissionSpec("FLIGHT-F1-RESEARCH", "Research & Intelligence Frontier", "sage/c2/frontier_intelligence_bridge.py", "sage/c2/frontier_intelligence/", "evidence_capture/f1_research_evidence.json", "F1 Autonomous Research", ["tests/c2/test_frontier_admission.py"]),
    FlightMissionSpec("FLIGHT-F2-CONTINUITY", "Continuity & Failure Memory Frontier", "sage/capability_registry.py", "sage/capability_registry.py", "evidence_capture/f2_continuity_evidence.json", "F2 Continuity Ledger", ["tests/test_capability_registry.py", "tests/test_capability_lineage.py"]),
    FlightMissionSpec("FLIGHT-F3-EXECUTION", "Execution & Substrate Frontier", "sage/runtime/engine.py", "sage/runtime/", "evidence_capture/f3_execution_evidence.json", "F3 Runtime Acceleration", ["tests/test_system_frame.py"]),
    FlightMissionSpec("FLIGHT-F4-GUARD", "Governance & Architecture Guard Frontier", "sage/c2/chatgpt_c2_contract.py", "sage/c2/contract/", "evidence_capture/f4_guard_evidence.json", "F4 Governance Sentinel", ["tests/c2/test_chatgpt_c2_exact_order_anti_drift.py"]),
    FlightMissionSpec("FLIGHT-F5-WAREHOUSE", "Capability Warehouse & Reconvergence Frontier", "sage/c2/reconvergence_synthesizer.py", "sage/c2/reconvergence/", "evidence_capture/f5_warehouse_evidence.json", "F5 Reconvergence Warehouse", ["tests/c2/test_reconvergence_synthesizer.py"]),
]


class BuildJumpWaveEngine:
    """Execute five bounded flights with fail-closed lifecycle evidence."""

    def __init__(self, storage_dir: str = "evidence_capture"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.admission_engine = FrontierAdmissionEngine()
        self.lock_manager = FlightCollisionLockManager()

    def get_current_head_sha(self) -> str:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError(f"Invalid git HEAD commit SHA: '{sha}'")
        return sha

    def execute_wave(self, wave_id: Optional[str] = None, missions: Optional[List[FlightMissionSpec]] = None) -> ReconvergenceEvidencePackage:
        head_sha = self.get_current_head_sha()
        w_id = wave_id or f"wave-big-jump-{int(time.time())}"
        active_missions = missions or CANONICAL_BIG_JUMP_MISSIONS
        if len(active_missions) != 5:
            raise ValueError(f"Big Jump Wave requires exactly 5 flight missions, got {len(active_missions)}")

        gps = FlightGPS(canonical_head_sha=head_sha)
        flight_summaries: List[FlightExecutionSummary] = []

        for spec in active_missions:
            candidate = FrontierCandidate(
                frontier_id=spec.flight_id,
                target=spec.target_path,
                source=f"Big Jump Wave {w_id}",
                state=FrontierState.UNSTARTED,
                base_sha=head_sha,
                dependencies=[],
                collision_zone=spec.collision_zone,
                evidence_required=[spec.evidence_ref],
                stop_condition="Milestone proof verified",
            )
            admission = self.admission_engine.classify_and_evaluate(candidate)
            manifest = FlightManifest(
                flight_id=spec.flight_id,
                capability_target=spec.target_path,
                base_sha=head_sha,
                ownership=OwnershipFingerprint(
                    files={spec.target_path},
                    modules={spec.collision_zone.replace('/', '.')},
                    artifacts={spec.evidence_ref},
                ),
                lifecycle=FlightLifecycle.ACTIVE,
            )
            gps.registry.register(manifest)
            lock_res = self.lock_manager.acquire_lock(
                FlightLockRequest(
                    session_id=w_id,
                    flight_id=spec.flight_id,
                    target_files=[spec.target_path],
                    target_namespaces=[spec.collision_zone],
                )
            )

            try:
                m1 = LifecycleMilestoneRecord(
                    stage=LifecycleStage.INTAKE_RECON,
                    passed=admission.admitted and lock_res.acquired,
                    evidence_ref=spec.evidence_ref,
                )
                m2 = LifecycleMilestoneRecord(
                    stage=LifecycleStage.BOUNDED_BUILD,
                    passed=lock_res.acquired,
                    evidence_ref=spec.target_path,
                )

                tests_passed = 0
                all_tests_ok = True
                if spec.test_references:
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", *spec.test_references],
                        capture_output=True,
                        text=True,
                    )
                    all_tests_ok = result.returncode == 0
                    match = re.search(r"(\d+)\s+passed", result.stdout)
                    if match:
                        tests_passed = int(match.group(1))

                m3 = LifecycleMilestoneRecord(
                    stage=LifecycleStage.VERIFY_PROOF,
                    passed=all_tests_ok,
                    evidence_ref=spec.test_references[0] if spec.test_references else spec.target_path,
                )

                evidence_dir = self.storage_dir / "waves" / w_id / head_sha
                evidence_dir.mkdir(parents=True, exist_ok=True)
                evidence_file = evidence_dir / f"{spec.flight_id}_receipt.json"
                flight_proof = {
                    "wave_id": w_id,
                    "flight_id": spec.flight_id,
                    "frontier_name": spec.frontier_name,
                    "target_path": spec.target_path,
                    "executed_head": head_sha,
                    "status": "PASS" if (admission.admitted and lock_res.acquired and all_tests_ok) else "FAIL",
                    "timestamp": time.time(),
                }
                evidence_file.write_text(json.dumps(flight_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")

                m4 = LifecycleMilestoneRecord(
                    stage=LifecycleStage.WAREHOUSE_PROMOTE,
                    passed=all_tests_ok,
                    evidence_ref=str(evidence_file),
                )
                flight_summaries.append(
                    FlightExecutionSummary(
                        flight_id=spec.flight_id,
                        target=spec.target_path,
                        classification="ACTIVE",
                        execution_result="PASS" if (admission.admitted and lock_res.acquired and all_tests_ok) else "FAIL",
                        exact_head=head_sha,
                        tests_passed=tests_passed,
                        evidence_ref=str(evidence_file),
                        pr_or_change=spec.pr_or_change,
                        lifecycle_milestones=[m1, m2, m3, m4],
                    )
                )
            finally:
                if lock_res.acquired:
                    self.lock_manager.release_lock(w_id, spec.flight_id)

        return C2ReconvergenceSynthesizer(wave_id=w_id).synthesize_reconvergence(flight_summaries)
