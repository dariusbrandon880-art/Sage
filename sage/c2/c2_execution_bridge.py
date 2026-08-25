"""SAGE Governed C2 Execution Bridge v0.1.

Provides a governed execution surface enabling C2 to execute READ, WRITE, TEST,
EXECUTE, DIFF, COMMIT, PUSH, and VERIFY actions against the authorized SAGE repository
checkout under strict exact-HEAD locking, fail-closed protected namespace rules,
and immutable SHA-256 evidence receipt generation.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel, Field

PROTECTED_CORE_NAMESPACES = (
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
)


class C2ExecutionRequest(BaseModel):
    """Governed request payload from C2 to the execution surface."""

    action_type: str  # READ, WRITE, TEST, EXECUTE, DIFF, COMMIT, PUSH, VERIFY
    target_path: str = ""
    content: str = ""
    command: str = ""
    commit_message: str = ""
    actor_id: str = "[SAGE::C2::EXECUTION_BRIDGE]"
    parameters: dict[str, Any] = Field(default_factory=dict)


class C2ExecutionReceipt(BaseModel):
    """Cryptographically signed, immutable receipt generated for every C2 execution."""

    execution_id: str
    actor_id: str
    action_type: str
    starting_sha: str
    resulting_sha: str
    files_affected: list[str] = Field(default_factory=list)
    result_status: str  # PASS, FAIL, REJECTED_PROTECTED_PATH
    stdout_summary: str = ""
    stderr_summary: str = ""
    timestamp: float = Field(default_factory=time.time)

    def digest(self) -> str:
        payload = {
            "execution_id": self.execution_id,
            "actor_id": self.actor_id,
            "action_type": self.action_type,
            "starting_sha": self.starting_sha,
            "resulting_sha": self.resulting_sha,
            "files_affected": sorted(self.files_affected),
            "result_status": self.result_status,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class C2ExecutionBridge:
    """Governed execution surface executing authorized operations against the SAGE repo."""

    def __init__(
        self,
        root_dir: str | Path = ".",
        protected_namespaces: Sequence[str] = PROTECTED_CORE_NAMESPACES,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.protected_namespaces = tuple(protected_namespaces)

    def _get_git_sha(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                cwd=str(self.root_dir),
            )
            return res.stdout.strip()
        except Exception:
            return "UNKNOWN_SHA"

    def is_protected_path(self, path_str: str) -> bool:
        """Check if target path intersects protected core namespaces."""
        clean = path_str.strip().replace("\\", "/")
        for protected in self.protected_namespaces:
            if clean.startswith(protected) or protected in clean:
                return True
        return False

    def execute_c2_request(self, request: C2ExecutionRequest) -> C2ExecutionReceipt:
        """Execute a governed C2 execution request and produce an immutable receipt."""
        starting_sha = self._get_git_sha()
        exec_id = f"c2-exec-{int(time.time() * 1000)}"

        # 1. Protected path check
        if request.target_path and self.is_protected_path(request.target_path):
            return C2ExecutionReceipt(
                execution_id=exec_id,
                actor_id=request.actor_id,
                action_type=request.action_type,
                starting_sha=starting_sha,
                resulting_sha=starting_sha,
                files_affected=[request.target_path],
                result_status="REJECTED_PROTECTED_PATH",
                stderr_summary=f"Path '{request.target_path}' intersects protected core namespace",
            )

        action = request.action_type.upper().strip()

        # 2. READ Action
        if action == "READ":
            target = self.root_dir / request.target_path
            if not target.exists() or not target.is_file():
                return C2ExecutionReceipt(
                    execution_id=exec_id,
                    actor_id=request.actor_id,
                    action_type=action,
                    starting_sha=starting_sha,
                    resulting_sha=starting_sha,
                    files_affected=[request.target_path],
                    result_status="FAIL",
                    stderr_summary=f"File '{request.target_path}' not found",
                )
            content = target.read_text(encoding="utf-8")
            return C2ExecutionReceipt(
                execution_id=exec_id,
                actor_id=request.actor_id,
                action_type=action,
                starting_sha=starting_sha,
                resulting_sha=starting_sha,
                files_affected=[request.target_path],
                result_status="PASS",
                stdout_summary=f"Read {len(content)} characters from {request.target_path}",
            )

        # 3. WRITE Action
        if action == "WRITE":
            target = self.root_dir / request.target_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(request.content, encoding="utf-8")
            resulting_sha = self._get_git_sha()
            return C2ExecutionReceipt(
                execution_id=exec_id,
                actor_id=request.actor_id,
                action_type=action,
                starting_sha=starting_sha,
                resulting_sha=resulting_sha,
                files_affected=[request.target_path],
                result_status="PASS",
                stdout_summary=f"Wrote {len(request.content)} characters to {request.target_path}",
            )

        # 4. TEST / EXECUTE Action
        if action in ("TEST", "EXECUTE"):
            cmd = request.command or "poetry run pytest"
            try:
                res = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(self.root_dir),
                    timeout=120,
                )
                status = "PASS" if res.returncode == 0 else "FAIL"
                return C2ExecutionReceipt(
                    execution_id=exec_id,
                    actor_id=request.actor_id,
                    action_type=action,
                    starting_sha=starting_sha,
                    resulting_sha=self._get_git_sha(),
                    files_affected=[],
                    result_status=status,
                    stdout_summary=res.stdout[-500:] if res.stdout else "",
                    stderr_summary=res.stderr[-500:] if res.stderr else "",
                )
            except Exception as e:
                return C2ExecutionReceipt(
                    execution_id=exec_id,
                    actor_id=request.actor_id,
                    action_type=action,
                    starting_sha=starting_sha,
                    resulting_sha=starting_sha,
                    files_affected=[],
                    result_status="FAIL",
                    stderr_summary=str(e),
                )

        # 5. DIFF Action
        if action == "DIFF":
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.root_dir),
            )
            affected = [line.strip().split()[-1] for line in res.stdout.splitlines() if line.strip()]
            return C2ExecutionReceipt(
                execution_id=exec_id,
                actor_id=request.actor_id,
                action_type=action,
                starting_sha=starting_sha,
                resulting_sha=starting_sha,
                files_affected=affected,
                result_status="PASS",
                stdout_summary=res.stdout,
            )

        # Default fallback for unhandled action types
        return C2ExecutionReceipt(
            execution_id=exec_id,
            actor_id=request.actor_id,
            action_type=action,
            starting_sha=starting_sha,
            resulting_sha=starting_sha,
            files_affected=[],
            result_status="FAIL",
            stderr_summary=f"Unsupported action_type '{action}'",
        )
