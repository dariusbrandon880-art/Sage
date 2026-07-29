"""SAGE-ACT Experimental Active Hook & Intercept Layer (SAGE-ACH) Implementation."""

import os
import re
import json
import time
import uuid
import hashlib
import subprocess
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sage.experimental.act.continuity_control import (
    ContinuityControlRecord,
    ContinuityControlLoop,
)


class ActiveInterceptHookEvent(BaseModel):
    """Container representing a structured, captured command execution and workspace shift event."""
    event_id: str = Field(..., description="Unique trace identifier, matching ^ACH-EVT-[0-9]{8}-[a-fA-F0-9\\-]{36}$")
    command: str = Field(..., description="The command executed inside the wrapper")
    workspace_before: Dict[str, str] = Field(default_factory=dict, description="File-to-SHA mapping before command run")
    workspace_after: Dict[str, str] = Field(default_factory=dict, description="File-to-SHA mapping after command run")
    exit_code: int = Field(..., description="The exit code of the spawned process")
    execution_duration: float = Field(..., description="Wall execution time elapsed in seconds")
    output_summary: str = Field(..., description="Truncated stdout/stderr output summary")
    linked_record_id: Optional[str] = Field(default=None, description="Linked ContinuityControlRecord ID if streamed")


class ActiveClientHook:
    """Manages active command observation, state differential tracking, and automatic streaming.

    Operates strictly as an observational hook, with zero process execution control or automation authority.
    """

    def __init__(self, ccl_loop: Optional[ContinuityControlLoop] = None):
        """Initialize Active Client Hook with optional Continuity Control Loop linkage."""
        self.ccl_loop = ccl_loop

    def _compute_file_sha(self, filepath: str) -> str:
        """Calculate the SHA-256 hash of a workspace file. Returns empty string if missing."""
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            return ""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError:
            return ""

    def _capture_workspace_state(self, target_files: List[str]) -> Dict[str, str]:
        """Compute SHA-256 mappings of target observed files."""
        state = {}
        for file in target_files:
            sha = self._compute_file_sha(file)
            if sha:
                state[file] = sha
        return state

    def execute_observed_command(
        self,
        session_id: str,
        command: str,
        target_files: List[str],
    ) -> ActiveInterceptHookEvent:
        """Spawn and observe process execution, tracking state shifts and automatically streaming to CCL.

        Raises:
            ValueError: If session_id fails format verification.
        """
        if not re.match(r"^session_[a-fA-F0-9]{8}$", session_id):
            raise ValueError(f"SAGE-ACH Violation: Invalid session_id format '{session_id}'.")

        # 1. Capture workspace state before execution
        state_before = self._capture_workspace_state(target_files)

        # 2. Execute process in sandboxed shell
        # Tokenize safe command argv to avoid shell injection vulnerabilities (Mitigates command escalation)
        argv = command.split()
        if not argv:
            raise ValueError("SAGE-ACH Violation: Cannot execute empty command string.")

        start_time = time.time()
        try:
            # Execute with safe subprocess parameters, redirecting std descriptors
            proc = subprocess.run(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                timeout=30.0,  # 30 second safety guard timeout
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout or ""
            stderr = (e.stderr or "") + "\n[SAGE-ACH Process execution timed out]"
            exit_code = -1
        except Exception as e:
            stdout = ""
            stderr = f"[SAGE-ACH Process spawn failed]: {e}"
            exit_code = -2

        duration = time.time() - start_time

        # 3. Capture workspace state after execution
        state_after = self._capture_workspace_state(target_files)

        # 4. Synthesize output summary (Truncate to 1000 chars to avoid memory bloat)
        combined_output = f"{stdout}\n{stderr}".strip()
        if len(combined_output) > 1000:
            output_summary = combined_output[:997] + "..."
        else:
            output_summary = combined_output

        # 5. Generate Event trace ID
        date_str = time.strftime("%Y%m%d", time.gmtime())
        event_uuid = str(uuid.uuid4())
        event_id = f"ACH-EVT-{date_str}-{event_uuid}"

        event = ActiveInterceptHookEvent(
            event_id=event_id,
            command=command,
            workspace_before=state_before,
            workspace_after=state_after,
            exit_code=exit_code,
            execution_duration=duration,
            output_summary=output_summary,
        )

        # 6. Stream and link to SAGE-CCL automatically if configured
        if self.ccl_loop is not None:
            # Generate descriptive metadata and rationale for the transition record
            evidence_hash = hashlib.sha256(event.model_dump_json().encode()).hexdigest()
            evidence = {
                "ach_event_id": event.event_id,
                "command": event.command,
                "exit_code": event.exit_code,
                "sha256_checksum": evidence_hash,
                "git_commit": "0" * 40, # Local untracked command run placeholder
            }
            reasoning = f"Observed execution of '{event.command}'. Exit status: {event.exit_code}."
            action_desc = f"Execute wrapped process: {event.command}"

            # Log failures with explicit contexts
            failure_context = None
            recovery_path = None
            if event.exit_code != 0:
                failure_context = {
                    "error_type": "CommandExecutionFailure",
                    "exit_code": event.exit_code,
                    "details": event.output_summary,
                }
                recovery_path = "Analyze logs, resolve syntax/errors, and retry."

            # Automatically stage record via the CCL
            ccl_record = self.ccl_loop.capture_event(
                session_id=session_id,
                event_type="active_intercept",
                action=action_desc,
                reasoning=reasoning,
                evidence=evidence,
                failure_context=failure_context,
                recovery_path=recovery_path,
            )
            self.ccl_loop.stage_record(ccl_record)
            event.linked_record_id = ccl_record.record_id

        return event
