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
from sage.c2.reusable_flight_slots import FlightMissionAssignment, SAGE_FLIGHT_SLOTS, validate_mission_assignments


class FlightMissionSpec(BaseModel):
    """A current-wave mission assigned to one reusable F1-F5 execution slot."""

    flight_id: str
    mission_id: str
    frontier_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: List[str] = Field(default_factory=list)


class BuildJumpWaveEngine:
    """Execute five bounded missions concurrently with fail-closed evidence.

    The engine intentionally has no canonical F1-F5 mission table. Every wave
    must supply an explicit, validated assignment so slot identity cannot
    silently become a permanent mission role.
    """

    _verification_process_lock = threading.Lock()

    def __init__(self, storage_dir: str = "evidence_capture", max_workers: int = 5):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.admission_engine = FrontierAdmissionEngine()
        self.lock_manager = FlightCollisionLockManager()
        self.max_workers = max(1, min(max_workers, 5))
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
        with self._lock_manager_guard:
            admission = self.admission_engine.classify_and_evaluate(candidate)
            gps = FlightGPS(canonical_head_sha=head_sha)
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
            blocker = None
            if spec.test_references:
                with self._verification_process_lock:
                    result = subprocess.run([sys.executable, "-m", "pytest", *spec.test_references], capture_output=True, text=True)
                all_tests_ok = result.returncode == 0
                match = re.search(r"(\d+)\s+passed", result.stdout)
                if match:
                    tests_passed = int(match.group(1))
                if not all_tests_ok:
                    blocker = (result.stdout + "\n" + result.stderr).strip()[-4000:]
            m3 = LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=all_tests_ok, evidence_ref=spec.test_references[0] if spec.test_references else spec.target_path)
            evidence_dir = self.storage_dir / "waves" / wave_id / head_sha
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_file = evidence_dir / f"{spec.flight_id}_receipt.json"
            flight_passed = admission.admitted and lock_res.acquired and all_tests_ok
            flight_proof = {"wave_id": wave_id, "flight_id": spec.flight_id, "mission_id": spec.mission_id, "frontier_name": spec.frontier_name, "target_path": spec.target_path, "executed_head": head_sha, "status": "PASS" if flight_passed else "FAIL", "blocker": blocker, "timestamp": time.time()}
            evidence_file.write_text(json.dumps(flight_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            m4 = LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=all_tests_ok, evidence_ref=str(evidence_file))
            return FlightExecutionSummary(flight_id=spec.flight_id, target=spec.target_path, classification="ACTIVE", execution_result="PASS" if flight_passed else "FAIL", exact_head=head_sha, tests_passed=tests_passed, evidence_ref=str(evidence_file), pr_or_change=spec.pr_or_change, lifecycle_milestones=[m1, m2, m3, m4], blocker=blocker)
        finally:
            if lock_res.acquired:
                with self._lock_manager_guard:
                    self.lock_manager.release_lock(wave_id, spec.flight_id)

    def execute_wave(self, wave_id: Optional[str] = None, missions: Optional[List[FlightMissionSpec]] = None) -> ReconvergenceEvidencePackage:
        """Execute an explicitly assigned five-mission wave.

        Omitting ``missions`` is intentionally rejected: there is no permanent
        F1-F5 mission assignment in the canonical engine.
        """

        if missions is None:
            raise ValueError("Big Jump Wave requires explicit current-wave mission assignments; no permanent F1-F5 mission table exists")
        if len(missions) != len(SAGE_FLIGHT_SLOTS):
            raise ValueError(f"Big Jump Wave requires exactly {len(SAGE_FLIGHT_SLOTS)} flight missions, got {len(missions)}")
        validated = validate_mission_assignments(
            [
                FlightMissionAssignment(
                    slot_id=spec.flight_id,
                    mission_id=spec.mission_id,
                    frontier_name=spec.frontier_name,
                    target_path=spec.target_path,
                    collision_zone=spec.collision_zone,
                    evidence_ref=spec.evidence_ref,
                    pr_or_change=spec.pr_or_change,
                    test_references=tuple(spec.test_references),
                )
                for spec in missions
            ]
        )
        assignment_by_slot = {item.slot_id: item for item in validated}
        ordered_missions = [next(spec for spec in missions if spec.flight_id == slot) for slot in SAGE_FLIGHT_SLOTS]
        for spec in ordered_missions:
            if spec.mission_id != assignment_by_slot[spec.flight_id].mission_id:
                raise ValueError(f"Mission assignment drift detected for {spec.flight_id}")

        head_sha = self.get_current_head_sha()
        w_id = wave_id or f"wave-big-jump-{int(time.time())}"
        summaries: dict[str, FlightExecutionSummary] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="sage-flight") as executor:
            futures = {executor.submit(self._run_flight, spec, w_id, head_sha): spec for spec in ordered_missions}
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    summaries[spec.flight_id] = future.result()
                except Exception as exc:
                    summaries[spec.flight_id] = FlightExecutionSummary(
                        flight_id=spec.flight_id, target=spec.target_path, classification="ACTIVE", execution_result="FAIL",
                        exact_head=head_sha, tests_passed=0, evidence_ref=spec.evidence_ref, pr_or_change=spec.pr_or_change,
                        lifecycle_milestones=[LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=False, evidence_ref=spec.evidence_ref)],
                        blocker=f"{type(exc).__name__}: {exc}",
                    )
        ordered_summaries = [summaries[spec.flight_id] for spec in ordered_missions]
        return C2ReconvergenceSynthesizer(wave_id=w_id).synthesize_reconvergence(ordered_summaries)
