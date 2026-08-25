"""Governed C2 Execution Bridge & Provenance Engine."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


PROTECTED_NAMESPACES = [
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
]


class C2ExecutionRequest(BaseModel):
    """Execution request submitted to C2 Execution Bridge."""

    request_id: str
    command: str  # READ, WRITE, TEST, EXECUTE, DIFF, COMMIT, PUSH, VERIFY
    target_path: str
    expected_head_sha: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    auth_token: Optional[str] = None


class C2ExecutionReceipt(BaseModel):
    """Cryptographically verifiable execution receipt returned by C2 Execution Bridge."""

    receipt_id: str
    request_id: str
    command: str
    target_path: str
    starting_head_sha: str
    resulting_head_sha: str
    status: str  # SUCCESS, REJECTED, FAILED
    output: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint for execution receipt."""
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
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class C2ExecutionBridge:
    """Governed execution bridge validating command parameters, head SHAs, and namespace permissions."""

    VALID_COMMANDS = {"READ", "WRITE", "TEST", "EXECUTE", "DIFF", "COMMIT", "PUSH", "VERIFY"}

    def __init__(
        self,
        current_head_sha: str = "b44b892",
        system_token: str = "SAGE_SYSTEM_AUTH_TOKEN",
    ):
        self.current_head_sha = current_head_sha
        self.system_token = system_token

    def execute(self, request: C2ExecutionRequest) -> C2ExecutionReceipt:
        """Execute request under strict exact-HEAD and namespace governance."""
        receipt_id = f"rcpt-exec-{request.request_id}-{time.time_ns()}"
        starting_sha = self.current_head_sha

        # 1. Validate Command Type
        if request.command.upper() not in self.VALID_COMMANDS:
            receipt = C2ExecutionReceipt(
                receipt_id=receipt_id,
                request_id=request.request_id,
                command=request.command,
                target_path=request.target_path,
                starting_head_sha=starting_sha,
                resulting_head_sha=starting_sha,
                status="REJECTED",
                error_message=f"Invalid command '{request.command}'. Must be one of {sorted(self.VALID_COMMANDS)}.",
            )
            receipt.receipt_hash = receipt.compute_hash()
            return receipt

        # 2. Validate exact-HEAD locking
        if request.expected_head_sha != starting_sha:
            receipt = C2ExecutionReceipt(
                receipt_id=receipt_id,
                request_id=request.request_id,
                command=request.command,
                target_path=request.target_path,
                starting_head_sha=starting_sha,
                resulting_head_sha=starting_sha,
                status="REJECTED",
                error_message=f"HEAD SHA drift mismatch. Request expected '{request.expected_head_sha}', current HEAD is '{starting_sha}'.",
            )
            receipt.receipt_hash = receipt.compute_hash()
            return receipt

        # 3. Validate Protected Namespace Mutations
        is_protected = any(request.target_path.startswith(ns) for ns in PROTECTED_NAMESPACES)
        if is_protected and request.command in {"WRITE", "COMMIT", "PUSH", "EXECUTE"}:
            if request.auth_token != self.system_token:
                receipt = C2ExecutionReceipt(
                    receipt_id=receipt_id,
                    request_id=request.request_id,
                    command=request.command,
                    target_path=request.target_path,
                    starting_head_sha=starting_sha,
                    resulting_head_sha=starting_sha,
                    status="REJECTED",
                    error_message=f"Unauthorized mutation attempt on protected path '{request.target_path}'.",
                )
                receipt.receipt_hash = receipt.compute_hash()
                return receipt

        # Simulate execution success
        resulting_sha = starting_sha
        if request.command == "COMMIT":
            resulting_sha = hashlib.sha256(f"{starting_sha}-{time.time_ns()}".encode()).hexdigest()[:7]
            self.current_head_sha = resulting_sha

        receipt = C2ExecutionReceipt(
            receipt_id=receipt_id,
            request_id=request.request_id,
            command=request.command,
            target_path=request.target_path,
            starting_head_sha=starting_sha,
            resulting_head_sha=resulting_sha,
            status="SUCCESS",
            output={"executed": True, "command": request.command, "path": request.target_path},
        )
        receipt.receipt_hash = receipt.compute_hash()
        return receipt
