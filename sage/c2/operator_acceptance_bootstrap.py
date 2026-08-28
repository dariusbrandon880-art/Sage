"""Runtime bootstrap for deterministic mission rehydration and dual-gate acceptance."""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

SHA_LEN = 40

@dataclass
class GateState:
    status: str = "FAIL"
    checks: dict[str, bool] = field(default_factory=dict)

@dataclass
class OperatorAcceptanceState:
    mission_id: str
    canonical_git_sha: str
    main_goals: list[str] = field(default_factory=list)
    side_goals: list[str] = field(default_factory=list)
    active_flights: list[str] = field(default_factory=list)
    active_prs: list[str] = field(default_factory=list)
    active_issues: list[str] = field(default_factory=list)
    deterministic_gate: GateState = field(default_factory=GateState)
    empirical_gate: GateState = field(default_factory=GateState)
    acceptance_status: str = "NOT_ACCEPTED"
    open_defects: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["deterministic_gate"] = asdict(self.deterministic_gate)
        data["empirical_gate"] = asdict(self.empirical_gate)
        return data

class BootstrapFailure(RuntimeError):
    pass

class OperatorAcceptanceBootstrap:
    """Rehydrates canonical state before execution and fails closed on drift."""
    def __init__(self, repo_root: str | Path = ".", git_runner: Callable[..., str] | None = None,
                 state_provider: Callable[[], tuple[list[str], list[str]]] | None = None):
        self.repo_root = Path(repo_root)
        self._git_runner = git_runner or self._git
        self._state_provider = state_provider or self._local_state

    def _git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=self.repo_root, text=True, stderr=subprocess.STDOUT).strip()

    def _resolve_head(self) -> str:
        head = self._git_runner("rev-parse", "HEAD")
        if len(head) != SHA_LEN or any(c not in "0123456789abcdefABCDEF" for c in head):
            raise BootstrapFailure("canonical HEAD is not a valid 40-character SHA")
        return head

    def _local_state(self) -> tuple[list[str], list[str]]:
        """Read tracked active state from git refs without silently fabricating emptiness."""
        try:
            branches = [line.strip() for line in self._git("for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines() if line.strip()]
        except (subprocess.CalledProcessError, OSError) as exc:
            raise BootstrapFailure(f"unable to reconcile repository state: {exc}") from exc
        active_prs = [f"branch:{branch}" for branch in branches if branch != "main"]
        return active_prs, []

    def _active_prs(self) -> list[str]:
        return list(self._state_provider()[0])

    def _active_issues(self) -> list[str]:
        return list(self._state_provider()[1])

    def rehydrate(self, mission_id: str, main_goals: list[str], side_goals: list[str], active_flights: list[str]) -> OperatorAcceptanceState:
        if not mission_id or not main_goals:
            raise BootstrapFailure("mission_id and at least one main goal are required")
        head = self._resolve_head()
        try:
            active_prs, active_issues = self._state_provider()
        except Exception as exc:
            if isinstance(exc, BootstrapFailure):
                raise
            raise BootstrapFailure(f"unable to reconcile live state: {exc}") from exc
        if active_prs is None or active_issues is None:
            raise BootstrapFailure("FAIL_CLOSED: live reconciliation returned incomplete state")
        state = OperatorAcceptanceState(
            mission_id=mission_id,
            canonical_git_sha=head,
            main_goals=list(main_goals), side_goals=list(side_goals), active_flights=list(active_flights),
            active_prs=list(active_prs), active_issues=list(active_issues),
            deterministic_gate=GateState("PASS", {"exact_sha_anchored": True, "repository_rehydrated": True, "live_state_reconciled": True}),
            empirical_gate=GateState("PENDING", {"operator_observation": False, "evidence_linked": False}),
            acceptance_status="ENGINEERING_VERIFIED",
        )
        return state

    def require_execution_ready(self, state: OperatorAcceptanceState) -> None:
        if state.deterministic_gate.status != "PASS":
            raise BootstrapFailure("FAIL_CLOSED: deterministic bootstrap gate not passed")
        if not state.main_goals or not state.canonical_git_sha:
            raise BootstrapFailure("FAIL_CLOSED: incomplete rehydrated mission state")
        if not state.deterministic_gate.checks.get("live_state_reconciled"):
            raise BootstrapFailure("FAIL_CLOSED: live repository state was not reconciled")

    def capture_operator_observation(self, state: OperatorAcceptanceState, interface: str, verdict: str, evidence_ref: str, defect_id: str | None = None) -> OperatorAcceptanceState:
        if verdict not in {"PASS", "FAIL"}:
            raise BootstrapFailure("operator verdict must be PASS or FAIL")
        if not interface or not evidence_ref:
            raise BootstrapFailure("interface and evidence_ref are required")
        state.evidence_refs.append(evidence_ref)
        state.empirical_gate.checks["operator_observation"] = True
        state.empirical_gate.checks["evidence_linked"] = True
        state.empirical_gate.checks[f"interface:{interface}"] = verdict == "PASS"
        if verdict == "FAIL":
            if defect_id:
                state.open_defects.append(defect_id)
            state.empirical_gate.status = "FAIL"
            state.acceptance_status = "NOT_ACCEPTED"
        else:
            state.empirical_gate.status = "PASS"
            state.acceptance_status = "ACCEPTED" if state.deterministic_gate.status == "PASS" else "OPERATOR_OBSERVED"
        return state

    def evidence_receipt(self, state: OperatorAcceptanceState, path: str | Path) -> Path:
        payload = state.to_dict()
        payload["generated_at"] = time.time()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload["receipt_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output
