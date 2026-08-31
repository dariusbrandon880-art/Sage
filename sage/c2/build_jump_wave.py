"""SAGE Big Jump Wave Engine with bounded parallel flight execution."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from sage.c2.experiment_ledger import ExperimentLedger
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
    """Specification of a dynamic flight mission assigned to a flight slot."""

    flight_id: str
    frontier_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: List[str] = Field(default_factory=list)


def create_default_wave_missions() -> List[FlightMissionSpec]:
    """Factory creating dynamic 5-flight mission specifications for Big Jump Wave execution."""
    return [
        FlightMissionSpec(
            flight_id="F1",
            frontier_name="Research & Intelligence Frontier",
            target_path="sage/c2/frontier_intelligence_bridge.py",
            collision_zone="sage/c2/frontier_intelligence/",
            evidence_ref="evidence_capture/f1_research_evidence.json",
            pr_or_change="F1 Dynamic Flight",
            test_references=["tests/c2/test_frontier_admission.py"],
        ),
        FlightMissionSpec(
            flight_id="F2",
            frontier_name="Continuity & Failure Memory Frontier",
            target_path="sage/capability_registry.py",
            collision_zone="sage/capability_registry.py",
            evidence_ref="evidence_capture/f2_continuity_evidence.json",
            pr_or_change="F2 Dynamic Flight",
            test_references=["tests/test_capability_registry.py"],
        ),
        FlightMissionSpec(
            flight_id="F3",
            frontier_name="Execution & Substrate Frontier",
            target_path="sage/runtime/engine.py",
            collision_zone="sage/runtime/",
            evidence_ref="evidence_capture/f3_execution_evidence.json",
            pr_or_change="F3 Dynamic Flight",
            test_references=["tests/test_system_frame.py"],
        ),
        FlightMissionSpec(
            flight_id="F4",
            frontier_name="Governance & Architecture Guard Frontier",
            target_path="sage/c2/chatgpt_c2_contract.py",
            collision_zone="sage/c2/contract/",
            evidence_ref="evidence_capture/f4_guard_evidence.json",
            pr_or_change="F4 Dynamic Flight",
            test_references=["tests/c2/test_chatgpt_c2_exact_order_anti_drift.py"],
        ),
        FlightMissionSpec(
            flight_id="F5",
            frontier_name="Capability Warehouse & Reconvergence Frontier",
            target_path="sage/c2/reconvergence_synthesizer.py",
            collision_zone="sage/c2/reconvergence/",
            evidence_ref="evidence_capture/f5_warehouse_evidence.json",
            pr_or_change="F5 Dynamic Flight",
            test_references=["tests/c2/test_reconvergence_synthesizer.py"],
        ),
    ]


class BuildJumpWaveEngine:
    """Execute five bounded flights concurrently with fail-closed evidence."""

    def __init__(
        self,
        storage_dir: str = "evidence_capture",
        max_workers: int = 5,
        experiment_ledger: Optional[ExperimentLedger] = None,
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.admission_engine = FrontierAdmissionEngine()
        self.lock_manager = FlightCollisionLockManager()
        self.max_workers = max(1, min(max_workers, 5))
        self.experiment_ledger = experiment_ledger or ExperimentLedger(
            ledger_path=str(self.storage_dir / "experiment_ledger.json")
        )
        self._lock_manager_guard = threading.Lock()

    def get_current_head_sha(self) -> str:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError(f"Invalid git HEAD commit SHA: '{sha}'")
        return sha

    def _run_flight(self, spec: FlightMissionSpec, wave_id: str, head_sha: str) -> FlightExecutionSummary:
        candidate = FrontierCandidate(
            frontier_id=spec.flight_id,
            target=spec.target_path,
            source=f"Big Jump Wave {wave_id}",
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
        with self._lock_manager_guard:
            gps = FlightGPS(canonical_head_sha=head_sha)
            gps.registry.register(manifest)
            lock_res = self.lock_manager.acquire_lock(
                FlightLockRequest(
                    session_id=wave_id,
                    flight_id=spec.flight_id,
                    target_files=[spec.target_path],
                    target_namespaces=[spec.collision_zone],
                )
            )

        try:
            m1 = LifecycleMilestoneRecord(stage=LifecycleStage.INTAKE_RECON, passed=admission.admitted and lock_res.acquired, evidence_ref=spec.evidence_ref)
            m2 = LifecycleMilestoneRecord(stage=LifecycleStage.BOUNDED_BUILD, passed=lock_res.acquired, evidence_ref=spec.target_path)

            tests_passed = 0
            all_tests_ok = True
            if spec.test_references:
                result = subprocess.run([sys.executable, "-m", "pytest", *spec.test_references], capture_output=True, text=True)
                all_tests_ok = result.returncode == 0
                match = re.search(r"(\d+)\s+passed", result.stdout)
                if match:
                    tests_passed = int(match.group(1))

            m3 = LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=all_tests_ok, evidence_ref=spec.test_references[0] if spec.test_references else spec.target_path)
            evidence_dir = self.storage_dir / "waves" / wave_id / head_sha
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_file = evidence_dir / f"{spec.flight_id}_receipt.json"
            flight_passed = admission.admitted and lock_res.acquired and all_tests_ok
            flight_proof = {"wave_id": wave_id, "flight_id": spec.flight_id, "frontier_name": spec.frontier_name, "target_path": spec.target_path, "executed_head": head_sha, "status": "PASS" if flight_passed else "FAIL", "timestamp": time.time()}
            evidence_file.write_text(json.dumps(flight_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            # Record flight receipt into ExperimentLedger fail-closed
            if self.experiment_ledger:
                self.experiment_ledger.record_flight_receipt(
                    wave_id=wave_id,
                    flight_id=spec.flight_id,
                    commit_sha=head_sha,
                    receipt_data={
                        "evidence_ref": str(evidence_file),
                        "target_path": spec.target_path,
                        "status": "PASS" if flight_passed else "FAIL",
                    },
                )

            m4 = LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=all_tests_ok, evidence_ref=str(evidence_file))
            return FlightExecutionSummary(flight_id=spec.flight_id, target=spec.target_path, classification="ACTIVE", execution_result="PASS" if flight_passed else "FAIL", exact_head=head_sha, tests_passed=tests_passed, evidence_ref=str(evidence_file), pr_or_change=spec.pr_or_change, lifecycle_milestones=[m1, m2, m3, m4])
        finally:
            if lock_res.acquired:
                with self._lock_manager_guard:
                    self.lock_manager.release_lock(wave_id, spec.flight_id)

    def execute_wave(
        self,
        wave_id: Optional[str] = None,
        missions: Optional[List[FlightMissionSpec]] = None,
    ) -> ReconvergenceEvidencePackage:
        """Execute exactly 5 dynamic flight missions concurrently."""
        head_sha = self.get_current_head_sha()
        w_id = wave_id or f"wave-big-jump-{int(time.time())}"
        active_missions = missions if missions is not None else create_default_wave_missions()
        if len(active_missions) != 5:
            raise ValueError(f"Big Jump Wave requires exactly 5 flight missions, got {len(active_missions)}")

        summaries: dict[str, FlightExecutionSummary] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="sage-flight") as executor:
            futures = {executor.submit(self._run_flight, spec, w_id, head_sha): spec for spec in active_missions}
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    summaries[spec.flight_id] = future.result()
                except Exception:
                    summaries[spec.flight_id] = FlightExecutionSummary(
                        flight_id=spec.flight_id, target=spec.target_path, classification="ACTIVE", execution_result="FAIL",
                        exact_head=head_sha, tests_passed=0, evidence_ref=spec.evidence_ref, pr_or_change=spec.pr_or_change,
                        lifecycle_milestones=[LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=False, evidence_ref=spec.evidence_ref)],
                    )

        ordered_summaries = [summaries[spec.flight_id] for spec in active_missions]
        return C2ReconvergenceSynthesizer(wave_id=w_id).synthesize_reconvergence(ordered_summaries)
