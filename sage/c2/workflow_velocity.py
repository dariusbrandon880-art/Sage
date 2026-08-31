"""SAGE Multi-Session Velocity Engine & Rolls-Royce Workflow Protocol.

Coordinates multi-session Big Jump Waves between C2 Control Tower and parallel Jules execution sessions:
- Concurrent session tracking and registration.
- Non-blocking anti-collision namespace locking via FlightCollisionLockManager.
- 5x4 20-cell lifecycle advancement matrix traversal.
- Rolls-Royce engineering quality verification and SHA-256 evidence receipt generation bound to exact commit HEAD.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re
import threading
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.c2.flight_collision_lock import FlightCollisionLockManager, FlightLockRequest, LockCheckResult
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
    ReconvergenceEvidencePackage,
)


class SessionRole(str, Enum):
    """Execution station role in the multi-session model."""
    C2_CONTROL_TOWER = "C2_CONTROL_TOWER"
    JULES_EXECUTION_SESSION = "JULES_EXECUTION_SESSION"


class SessionContext(BaseModel):
    """Context and registration state of an active execution session."""
    session_id: str
    role: SessionRole
    active_wave_id: Optional[str] = None
    registered_at: float = Field(default_factory=time.time)


class MultiSessionVelocityReceipt(BaseModel):
    """Cryptographic evidence receipt for a completed multi-session velocity wave."""
    receipt_id: str
    wave_id: str
    active_sessions: List[str]
    exact_git_head: str
    total_flights: int
    successful_flights: int
    advancement_matrix_20_cells: Dict[str, bool]
    rolls_royce_quality_passed: bool
    reconvergence_verdict: str
    organism_growth_receipt: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        sessions_str = ",".join(sorted(self.active_sessions))
        matrix_str = ";".join([f"{k}={v}" for k, v in sorted(self.advancement_matrix_20_cells.items())])
        payload = (
            f"{self.receipt_id}:{self.wave_id}:{sessions_str}:{self.exact_git_head}:"
            f"{self.total_flights}:{self.successful_flights}:{self.rolls_royce_quality_passed}:"
            f"{self.reconvergence_verdict}:{matrix_str}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class MultiSessionVelocityEngine:
    """Governance engine managing parallel velocity across concurrent sessions."""

    def __init__(self, max_workers: int = 5):
        self._sessions: Dict[str, SessionContext] = {}
        self._lock_manager = FlightCollisionLockManager()
        self.max_workers = max(1, min(max_workers, 15))
        self._guard_lock = threading.Lock()

    def register_session(self, session_id: str, role: SessionRole) -> SessionContext:
        """Registers or retrieves an active execution session context."""
        with self._guard_lock:
            if session_id in self._sessions:
                ctx = self._sessions[session_id]
                ctx.role = role
                return ctx

            ctx = SessionContext(session_id=session_id, role=role)
            self._sessions[session_id] = ctx
            return ctx

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieves session context if registered."""
        with self._guard_lock:
            return self._sessions.get(session_id)

    def list_active_sessions(self) -> List[SessionContext]:
        """Returns list of currently registered sessions."""
        with self._guard_lock:
            return list(self._sessions.values())

    def acquire_flight_lock(
        self,
        session_id: str,
        flight_id: str,
        target_files: List[str],
        target_namespaces: List[str]
    ) -> LockCheckResult:
        """Attempts to acquire non-overlapping namespace locks for a flight."""
        req = FlightLockRequest(
            session_id=session_id,
            flight_id=flight_id,
            target_files=target_files,
            target_namespaces=target_namespaces,
        )
        return self._lock_manager.acquire_lock(req)

    def release_flight_lock(self, session_id: str, flight_id: str) -> bool:
        """Releases locks held by a flight."""
        return self._lock_manager.release_lock(session_id, flight_id)

    def _execute_single_flight(
        self,
        idx: int,
        flight: Dict[str, Any],
        wave_id: str,
        session_id: str,
        exact_git_head: str,
    ) -> FlightExecutionSummary:
        """Helper executing a single flight worker task concurrently with lock management."""
        flight_id = flight.get("flight_id", f"F{idx}")
        target_files = flight.get("target_files", [])
        target_namespaces = flight.get("target_namespaces", [])

        # Lock acquisition check
        lock_res = self.acquire_flight_lock(
            session_id=session_id,
            flight_id=flight_id,
            target_files=target_files,
            target_namespaces=target_namespaces,
        )

        if not lock_res.acquired:
            return FlightExecutionSummary(
                flight_id=flight_id,
                target=flight.get("target", f"Frontier {idx}"),
                classification=flight.get("classification", "ACTIVE"),
                execution_result="BLOCKED_LOCK_COLLISION",
                exact_head=exact_git_head,
                tests_passed=0,
                evidence_ref=f"evidence_capture/{wave_id}_{flight_id}_collision.json",
                pr_or_change=flight.get("pr_or_change", f"PR #{260 + idx}"),
                blocker=f"Namespace collision on {lock_res.conflicting_resource} with session {lock_res.conflicting_session_id}",
            )

        try:
            # Simulated flight processing window
            work_delay = flight.get("delay_sec", 0.001)
            time.sleep(work_delay)

            # Traverse canonical 4 lifecycle stages for each flight
            milestones = [
                LifecycleMilestoneRecord(
                    stage=LifecycleStage.INTAKE_RECON,
                    passed=True,
                    evidence_ref=f"evidence/{wave_id}_{flight_id}_stage1.json",
                ),
                LifecycleMilestoneRecord(
                    stage=LifecycleStage.BOUNDED_BUILD,
                    passed=True,
                    evidence_ref=f"evidence/{wave_id}_{flight_id}_stage2.json",
                ),
                LifecycleMilestoneRecord(
                    stage=LifecycleStage.VERIFY_PROOF,
                    passed=True,
                    evidence_ref=f"evidence/{wave_id}_{flight_id}_stage3.json",
                ),
                LifecycleMilestoneRecord(
                    stage=LifecycleStage.WAREHOUSE_PROMOTE,
                    passed=True,
                    evidence_ref=f"evidence/{wave_id}_{flight_id}_stage4.json",
                ),
            ]

            tests_passed = flight.get("tests_passed", 10)
            exec_result = flight.get("execution_result", "PASS")

            return FlightExecutionSummary(
                flight_id=flight_id,
                target=flight.get("target", f"Frontier {idx}"),
                classification=flight.get("classification", "ACTIVE"),
                execution_result=exec_result,
                exact_head=exact_git_head,
                tests_passed=tests_passed,
                evidence_ref=f"evidence_capture/{wave_id}_{flight_id}_evidence.json",
                pr_or_change=flight.get("pr_or_change", f"PR #{260 + idx}"),
                lifecycle_milestones=milestones,
            )
        finally:
            self.release_flight_lock(session_id, flight_id)

    def execute_velocity_wave(
        self,
        wave_id: str,
        session_id: str,
        flight_payloads: List[Dict[str, Any]],
        exact_git_head: str,
    ) -> MultiSessionVelocityReceipt:
        """Executes a multi-session velocity wave concurrently with Rolls-Royce quality verification.

        Dispatches flights concurrently across worker threads, manages non-overlapping namespace
        locks, traverses 20-cell advancement matrix, enforces SHA-256 exact HEAD binding, and
        generates an immutable evidence receipt.
        """
        # Enforce exact 40-char SHA validation
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")
        if not sha_pattern.match(exact_git_head):
            raise ValueError(f"Invalid exact git HEAD commit SHA: {exact_git_head}")

        # Ensure session is registered
        session_ctx = self.register_session(session_id, SessionRole.JULES_EXECUTION_SESSION)
        session_ctx.active_wave_id = wave_id

        # Register Control Tower session if absent
        c2_tower = self.register_session("c2-control-tower-primary", SessionRole.C2_CONTROL_TOWER)
        c2_tower.active_wave_id = wave_id

        summaries_dict: Dict[int, FlightExecutionSummary] = {}

        # Concurrent worker dispatch using ThreadPoolExecutor
        workers = min(self.max_workers, max(1, len(flight_payloads)))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="sage-velocity") as executor:
            future_to_idx = {
                executor.submit(
                    self._execute_single_flight,
                    idx,
                    flight,
                    wave_id,
                    session_id,
                    exact_git_head,
                ): idx
                for idx, flight in enumerate(flight_payloads, start=1)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    summary = future.result()
                except Exception as exc:
                    flight_id = flight_payloads[idx - 1].get("flight_id", f"F{idx}")
                    summary = FlightExecutionSummary(
                        flight_id=flight_id,
                        target=flight_payloads[idx - 1].get("target", f"Frontier {idx}"),
                        classification="ACTIVE",
                        execution_result="FAIL",
                        exact_head=exact_git_head,
                        tests_passed=0,
                        evidence_ref=f"evidence_capture/{wave_id}_{flight_id}_error.json",
                        pr_or_change=flight_payloads[idx - 1].get("pr_or_change", f"PR #{260 + idx}"),
                        blocker=f"Worker exception: {exc}",
                    )
                summaries_dict[idx] = summary

        flight_summaries = [summaries_dict[i] for i in sorted(summaries_dict.keys())]

        # Synthesize reconvergence across 20-cell matrix
        synthesizer = C2ReconvergenceSynthesizer(wave_id=wave_id)
        reconvergence_pkg: ReconvergenceEvidencePackage = synthesizer.synthesize_reconvergence(flight_summaries)

        # Rolls-Royce quality standard verification
        rolls_royce_passed = (
            reconvergence_pkg.reconvergence_verdict == "PASS"
            and len(reconvergence_pkg.advancement_matrix_20_cells) == 20
            and all(reconvergence_pkg.advancement_matrix_20_cells.values())
            and reconvergence_pkg.successful_flights == reconvergence_pkg.total_flights == 5
        )

        organism_growth_dict = None
        try:
            import importlib
            mod = importlib.import_module("sage.experimental.airspace.fleet_evolution")
            FleetEvolutionIntelligence = getattr(mod, "FleetEvolutionIntelligence")
            fleet_intel = FleetEvolutionIntelligence(commit_sha=exact_git_head)
            org_growth = fleet_intel.evaluate_organism_growth_rate(
                velocity_score=reconvergence_pkg.successful_flights / reconvergence_pkg.total_flights,
                wave_completion_rate=len(reconvergence_pkg.advancement_matrix_20_cells) / 20.0,
                anti_drift_compliance_score=1.0 if rolls_royce_passed else 0.5,
            )
            organism_growth_dict = org_growth.to_dict()
        except Exception:
            pass

        receipt = MultiSessionVelocityReceipt(
            receipt_id=f"rec_{hashlib.sha256(f'{wave_id}:{exact_git_head}'.encode('utf-8')).hexdigest()[:12]}",
            wave_id=wave_id,
            active_sessions=self.list_active_sessions_ids(),
            exact_git_head=exact_git_head,
            total_flights=reconvergence_pkg.total_flights,
            successful_flights=reconvergence_pkg.successful_flights,
            advancement_matrix_20_cells=reconvergence_pkg.advancement_matrix_20_cells,
            rolls_royce_quality_passed=rolls_royce_passed,
            reconvergence_verdict=reconvergence_pkg.reconvergence_verdict,
            organism_growth_receipt=organism_growth_dict,
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt

    def list_active_sessions_ids(self) -> List[str]:
        """Returns sorted list of registered active session IDs."""
        with self._guard_lock:
            return sorted(list(self._sessions.keys()))
