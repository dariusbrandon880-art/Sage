"""Governed C2 Execution Bridge & Provenance Engine.

This component is a governance/simulation boundary. It validates exact-HEAD claims,
protected namespace authorization, and produces hashed execution receipts; it does not
perform real GitHub writes or mutate the repository itself.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


PROTECTED_NAMESPACES = ["sage/core/", "sage/runtime/", "sage/acr/", "sage/agents/"]


class C2ExecutionRequest(BaseModel):
    request_id: str
    command: str
    target_path: str
    expected_head_sha: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    auth_token: Optional[str] = None


class C2ExecutionReceipt(BaseModel):
    receipt_id: str
    request_id: str
    command: str
    target_path: str
    starting_head_sha: str
    resulting_head_sha: str
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "command": self.command,
            "target_path": self.target_path,
            "starting_head_sha": self.starting_head_sha,
            "resulting_head_sha": self.resulting_head_sha,
            "status": self.status,
            "error_message": self.error_message,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class C2ExecutionBridge:
    """Validates command parameters, exact HEAD claims, and namespace permissions."""

    VALID_COMMANDS = {"READ", "WRITE", "TEST", "EXECUTE", "DIFF", "COMMIT", "PUSH", "VERIFY"}

    def __init__(self, current_head_sha: str, system_token: str = "SAGE_SYSTEM_AUTH_TOKEN"):
        if not current_head_sha or len(current_head_sha) != 40:
            raise ValueError("current_head_sha must be the active 40-character repository HEAD SHA")
        self.current_head_sha = current_head_sha
        self.system_token = system_token

    def execute(self, request: C2ExecutionRequest) -> C2ExecutionReceipt:
        receipt_id = f"rcpt-exec-{request.request_id}-{time.time_ns()}"
        starting_sha = self.current_head_sha
        command = request.command.upper()

        def reject(message: str) -> C2ExecutionReceipt:
            receipt = C2ExecutionReceipt(
                receipt_id=receipt_id,
                request_id=request.request_id,
                command=request.command,
                target_path=request.target_path,
                starting_head_sha=starting_sha,
                resulting_head_sha=starting_sha,
                status="REJECTED",
                error_message=message,
            )
            receipt.receipt_hash = receipt.compute_hash()
            return receipt

        if command not in self.VALID_COMMANDS:
            return reject(f"Invalid command '{request.command}'. Must be one of {sorted(self.VALID_COMMANDS)}.")

        if request.expected_head_sha not in {starting_sha, starting_sha[:7]}:
            return reject(f"HEAD SHA drift mismatch. Request expected '{request.expected_head_sha}', current HEAD is '{starting_sha}'.")

        is_protected = any(request.target_path.startswith(ns) for ns in PROTECTED_NAMESPACES)
        if is_protected and command in {"WRITE", "COMMIT", "PUSH", "EXECUTE"} and request.auth_token != self.system_token:
            return reject(f"Unauthorized mutation attempt on protected path '{request.target_path}'.")

        resulting_sha = starting_sha
        output: Dict[str, Any] = {"executed": True, "command": command, "path": request.target_path, "simulation": True}
        if command == "COMMIT":
            resulting_sha = hashlib.sha256(f"{starting_sha}-{time.time_ns()}".encode()).hexdigest()
            self.current_head_sha = resulting_sha
            output["simulation"] = True

        receipt = C2ExecutionReceipt(
            receipt_id=receipt_id,
            request_id=request.request_id,
            command=request.command,
            target_path=request.target_path,
            starting_head_sha=starting_sha,
            resulting_head_sha=resulting_sha,
            status="SUCCESS",
            output=output,
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt
