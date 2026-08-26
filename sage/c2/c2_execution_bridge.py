"""Governed C2 Execution Bridge & Provenance Engine.

This module models governed execution decisions and receipts; it does not perform
arbitrary host or Git operations itself.
"""

import hashlib
import json
import re
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

PROTECTED_NAMESPACES = ["sage/core/", "sage/runtime/", "sage/acr/", "sage/agents/"]
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")

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
        payload = {"receipt_id": self.receipt_id, "request_id": self.request_id, "command": self.command, "target_path": self.target_path, "starting_head_sha": self.starting_head_sha, "resulting_head_sha": self.resulting_head_sha, "status": self.status, "error_message": self.error_message}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

class C2ExecutionBridge:
    """Validates commands, exact 40-character HEAD identity and protected namespaces."""
    VALID_COMMANDS = {"READ", "WRITE", "TEST", "EXECUTE", "DIFF", "COMMIT", "PUSH", "VERIFY"}

    def __init__(self, current_head_sha: str, system_token: str = "SAGE_SYSTEM_AUTH_TOKEN"):
        if not SHA40.fullmatch(current_head_sha):
            raise ValueError("current_head_sha must be an exact 40-character hexadecimal SHA")
        self.current_head_sha = current_head_sha.lower()
        self.system_token = system_token

    def _receipt(self, request: C2ExecutionRequest, status: str, error: Optional[str] = None, resulting_sha: Optional[str] = None, output: Optional[Dict[str, Any]] = None) -> C2ExecutionReceipt:
        receipt = C2ExecutionReceipt(receipt_id=f"rcpt-exec-{request.request_id}-{time.time_ns()}", request_id=request.request_id, command=request.command, target_path=request.target_path, starting_head_sha=self.current_head_sha, resulting_head_sha=resulting_sha or self.current_head_sha, status=status, error_message=error, output=output or {})
        receipt.receipt_hash = receipt.compute_hash()
        return receipt

    def execute(self, request: C2ExecutionRequest) -> C2ExecutionReceipt:
        if request.command.upper() not in self.VALID_COMMANDS:
            return self._receipt(request, "REJECTED", f"Invalid command '{request.command}'. Must be one of {sorted(self.VALID_COMMANDS)}.")
        if not SHA40.fullmatch(request.expected_head_sha) or request.expected_head_sha.lower() != self.current_head_sha:
            return self._receipt(request, "REJECTED", f"HEAD SHA drift mismatch. Request expected '{request.expected_head_sha}', current HEAD is '{self.current_head_sha}'.")
        protected = any(request.target_path.startswith(ns) for ns in PROTECTED_NAMESPACES)
        if protected and request.command.upper() in {"WRITE", "COMMIT", "PUSH", "EXECUTE"} and request.auth_token != self.system_token:
            return self._receipt(request, "REJECTED", f"Unauthorized mutation attempt on protected path '{request.target_path}'.")
        resulting = self.current_head_sha
        if request.command.upper() == "COMMIT":
            resulting = hashlib.sha256(f"{self.current_head_sha}:{request.request_id}:{time.time_ns()}".encode()).hexdigest()
            self.current_head_sha = resulting
        return self._receipt(request, "SUCCESS", resulting_sha=resulting, output={"simulated": True, "command": request.command, "path": request.target_path})
