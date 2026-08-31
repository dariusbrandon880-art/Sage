"""SAGE Big Jump Wave Engine with concurrent five-flight execution."""

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


BIG_JUMP_FLIGHT_IDS = ("F1", "F2", "F3", "F4", "F5")


class FlightMissionSpec(BaseModel):
    """A wave-assigned mission; flight IDs are reusable execution slots, not roles."""

    flight_id: str
    mission_name: str
    target_path: str
    collision_zone: str
    evidence_ref: str
    pr_or_change: str
    test_references: List[str] = Field(default_factory=list)


class BuildJumpWaveEngine:
    """Execute five independently assigned missions concurrently with fail-closed evidence."""

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
            flight_proof = {"wave_id": wave_id, "flight_id": spec.flight_id, "mission_name": spec.mission_name, "target_path": spec.target_path, "executed_head": head_sha, "status": "PASS" if flight_passed else "FAIL", "blocker": blocker, "timestamp": time.time()}
            evidence_file.write_text(json.dumps(flight_proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            m4 = LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=all_tests_ok, evidence_ref=str(evidence_file))
            return FlightExecutionSummary(flight_id=spec.flight_id, target=spec.target_path, classification="ACTIVE", execution_result="PASS" if flight_passed else "FAIL", exact_head=head_sha, tests_passed=tests_passed, evidence_ref=str(evidence_file), pr_or_change=spec.pr_or_change, lifecycle_milestones=[m1, m2, m3, m4], blocker=blocker)
        finally:
            if lock_res.acquired:
                with self._lock_manager_guard:
                    self.lock_manager.release_lock(wave_id, spec.flight_id)

    def execute_wave(self, wave_id: Optional[str] = None, missions: Optional[List[FlightMissionSpec]] = None) -> ReconvergenceEvidencePackage:
        head_sha = self.get_current_head_sha()
        w_id = wave_id or f"wave-big-jump-{int(time.time())}"
        if missions is None:
            raise ValueError("Big Jump Wave requires five wave-assigned missions; flight slots have no permanent roles")
        if len(missions) != 5:
            raise ValueError(f"Big Jump Wave requires exactly 5 flight missions, got {len(missions)}")
        mission_ids = [spec.flight_id for spec in missions]
        if set(mission_ids) != set(BIG_JUMP_FLIGHT_IDS):
            raise ValueError(f"Big Jump Wave requires exactly flight slots {BIG_JUMP_FLIGHT_IDS}, got {mission_ids}")
        if len(set(mission_ids)) != 5:
            raise ValueError("Big Jump Wave flight slots must be unique")
        summaries: dict[str, FlightExecutionSummary] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="sage-flight") as executor:
            futures = {executor.submit(self._run_flight, spec, w_id, head_sha): spec for spec in missions}
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
        ordered_summaries = [summaries[spec.flight_id] for spec in missions]
        return C2ReconvergenceSynthesizer(wave_id=w_id).synthesize_reconvergence(ordered_summaries)
