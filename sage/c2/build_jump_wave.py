"""SAGE Big Jump Wave Engine.

Coordinates 5 independent capability flight vectors operating across the canonical 5x4 lifecycle
advancement matrix (20 cells total) with exact-HEAD SHA provenance, Flight GPS clearance,
anti-collision locking, and fail-closed reconvergence synthesis.
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
    """Specification for an independent flight mission in a Big Jump Wave."""
    flight_id: str
    frontier_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: List[str] = Field(default_factory=list)


CANONICAL_BIG_JUMP_MISSIONS: List[FlightMissionSpec] = [
    FlightMissionSpec(
        flight_id="FLIGHT-F1-RESEARCH",
        frontier_name="Research & Intelligence Frontier",
        target_path="sage/c2/frontier_intelligence_bridge.py",
        collision_zone="sage/c2/frontier_intelligence/",
        evidence_ref="evidence_capture/f1_research_evidence.json",
        pr_or_change="F1 Autonomous Research",
        test_references=["tests/c2/test_frontier_admission.py"],
    ),
    FlightMissionSpec(
        flight_id="FLIGHT-F2-CONTINUITY",
        frontier_name="Continuity & Failure Memory Frontier",
        target_path="sage/capability_registry.py",
        collision_zone="sage/capability_registry.py",
        evidence_ref="evidence_capture/f2_continuity_evidence.json",
        pr_or_change="F2 Continuity Ledger",
        test_references=["tests/test_capability_registry.py", "tests/test_capability_lineage.py"],
    ),
    FlightMissionSpec(
        flight_id="FLIGHT-F3-EXECUTION",
        frontier_name="Execution & Substrate Frontier",
        target_path="sage/runtime/engine.py",
        collision_zone="sage/runtime/",
        evidence_ref="evidence_capture/f3_execution_evidence.json",
        pr_or_change="F3 Runtime Acceleration",
        test_references=["tests/test_system_frame.py"],
    ),
    FlightMissionSpec(
        flight_id="FLIGHT-F4-GUARD",
        frontier_name="Governance & Architecture Guard Frontier",
        target_path="sage/c2/chatgpt_c2_contract.py",
        collision_zone="sage/c2/contract/",
        evidence_ref="evidence_capture/f4_guard_evidence.json",
        pr_or_change="F4 Governance Sentinel",
        test_references=["tests/c2/test_chatgpt_c2_exact_order_anti_drift.py"],
    ),
    FlightMissionSpec(
        flight_id="FLIGHT-F5-WAREHOUSE",
        frontier_name="Capability Warehouse & Reconvergence Frontier",
        target_path="sage/c2/reconvergence_synthesizer.py",
        collision_zone="sage/c2/reconvergence/",
        evidence_ref="evidence_capture/f5_warehouse_evidence.json",
        pr_or_change="F5 Reconvergence Warehouse",
        test_references=["tests/c2/test_reconvergence_synthesizer.py"],
    ),
]


class BuildJumpWaveEngine:
    """Engine executing authorized 5-flight Big Jump Waves under Rolls-Royce engineering standards."""

    def __init__(self, storage_dir: str = "evidence_capture"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.admission_engine = FrontierAdmissionEngine()
        self.lock_manager = FlightCollisionLockManager()

    def get_current_head_sha(self) -> str:
        """Retrieve current exact 40-character git commit HEAD SHA."""
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = res.stdout.strip()
        if len(sha) != 40 or not re.match(r"^[0-9a-fA-F]{40}$", sha):
            raise ValueError(f"Invalid git HEAD commit SHA: '{sha}'")
        return sha

    def execute_wave(
        self,
        wave_id: Optional[str] = None,
        missions: Optional[List[FlightMissionSpec]] = None,
    ) -> ReconvergenceEvidencePackage:
        """Executes a 5-flight Big Jump Wave across all 4 canonical lifecycle gates (20 cells total)."""
        head_sha = self.get_current_head_sha()
        w_id = wave_id or f"wave-big-jump-{int(time.time())}"
        active_missions = missions or CANONICAL_BIG_JUMP_MISSIONS

        if len(active_missions) != 5:
            raise ValueError(f"Big Jump Wave requires exactly 5 flight missions, got {len(active_missions)}")

        gps = FlightGPS(canonical_head_sha=head_sha)
        flight_summaries: List[FlightExecutionSummary] = []

        for spec in active_missions:
            # Stage 1: INTAKE_RECON
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

            # Register with GPS and acquire collision lock
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

            lock_req = FlightLockRequest(
                session_id=w_id,
                flight_id=spec.flight_id,
                target_files=[spec.target_path],
                target_namespaces=[spec.collision_zone],
            )
            lock_res = self.lock_manager.acquire_lock(lock_req)

            m1 = LifecycleMilestoneRecord(
                stage=LifecycleStage.INTAKE_RECON,
                passed=admission.admitted and lock_res.acquired,
                evidence_ref=spec.evidence_ref,
            )

            # Stage 2: BOUNDED_BUILD
            m2 = LifecycleMilestoneRecord(
                stage=LifecycleStage.BOUNDED_BUILD,
                passed=lock_res.acquired,
                evidence_ref=spec.target_path,
            )

            # Stage 3: VERIFY_PROOF
            tests_passed = 0
            all_tests_ok = True
            if spec.test_references:
                pytest_cmd = ["poetry", "run", "pytest"] + spec.test_references
                res = subprocess.run(pytest_cmd, capture_output=True, text=True)
                all_tests_ok = (res.returncode == 0)
                # Parse test count from stdout if available
                match = re.search(r"(\d+)\s+passed", res.stdout)
                if match:
                    tests_passed = int(match.group(1))

            m3 = LifecycleMilestoneRecord(
                stage=LifecycleStage.VERIFY_PROOF,
                passed=all_tests_ok,
                evidence_ref=spec.test_references[0] if spec.test_references else spec.target_path,
            )

            # Stage 4: WAREHOUSE_PROMOTE
            evidence_file = self.storage_dir / Path(spec.evidence_ref).name
            flight_proof = {
                "flight_id": spec.flight_id,
                "frontier_name": spec.frontier_name,
                "target_path": spec.target_path,
                "exact_head": head_sha,
                "status": "PASS" if (admission.admitted and lock_res.acquired and all_tests_ok) else "FAIL",
                "timestamp": time.time(),
            }
            evidence_file.write_text(json.dumps(flight_proof, indent=2), encoding="utf-8")

            m4 = LifecycleMilestoneRecord(
                stage=LifecycleStage.WAREHOUSE_PROMOTE,
                passed=all_tests_ok,
                evidence_ref=str(evidence_file),
            )

            summary = FlightExecutionSummary(
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
            flight_summaries.append(summary)

        synthesizer = C2ReconvergenceSynthesizer(wave_id=w_id)
        evidence_pkg = synthesizer.synthesize_reconvergence(flight_summaries)
        return evidence_pkg
