"""Governed C2 Execution Surface Engine."""

from __future__ import annotations

import hashlib
import re
import subprocess
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class C2CommandType(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    TEST = "TEST"
    EXECUTE = "EXECUTE"
    DIFF = "DIFF"
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    VERIFY = "VERIFY"


class C2ExecutionRequest(BaseModel):
    request_id: str
    command_type: C2CommandType
    target_path: str
    starting_git_head: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class C2ExecutionSurfaceReceipt(BaseModel):
    receipt_id: str
    request_id: str
    command_type: C2CommandType
    target_path: str
    starting_git_head: str
    resulting_git_head: str
    status: str
    rejection_reason: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        payload = (
            f"{self.receipt_id}:{self.request_id}:{self.command_type.value}:{self.target_path}:"
            f"{self.starting_git_head}:{self.resulting_git_head}:{self.status}:{self.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class C2ExecutionSurfaceEngine:
    PROTECTED_NAMESPACES = (
        "sage/core/",
        "sage/runtime/",
        "sage/acr/",
        "sage/agents/",
    )
    SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")

    def __init__(self):
        self.receipts: List[C2ExecutionSurfaceReceipt] = []

    @staticmethod
    def resolve_runtime_head() -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    def _receipt(self, request: C2ExecutionRequest, status: str, reason: Optional[str] = None) -> C2ExecutionSurfaceReceipt:
        receipt = C2ExecutionSurfaceReceipt(
            receipt_id=f"c2_exec_rcpt_{int(time.time() * 1000)}",
            request_id=request.request_id,
            command_type=request.command_type,
            target_path=request.target_path,
            starting_git_head=request.starting_git_head,
            resulting_git_head=request.starting_git_head,
            status=status,
            rejection_reason=reason,
        )
        receipt.receipt_hash = receipt.compute_hash()
        self.receipts.append(receipt)
        return receipt

    def execute_request(self, request: C2ExecutionRequest) -> C2ExecutionSurfaceReceipt:
        if not self.SHA_PATTERN.fullmatch(request.starting_git_head):
            return self._receipt(request, "REJECTED_INVALID_SHA", f"Invalid starting git HEAD SHA: '{request.starting_git_head}'")
        runtime_head = self.resolve_runtime_head()
        if not self.SHA_PATTERN.fullmatch(runtime_head):
            return self._receipt(request, "REJECTED_UNOBSERVED_HEAD", "Unable to resolve executing repository HEAD")
        if request.starting_git_head.lower() != runtime_head.lower():
            return self._receipt(request, "REJECTED_STALE_HEAD", f"Requested HEAD '{request.starting_git_head}' does not equal runtime HEAD '{runtime_head}'")
        if request.command_type in (C2CommandType.WRITE, C2CommandType.COMMIT, C2CommandType.PUSH):
            for namespace in self.PROTECTED_NAMESPACES:
                if request.target_path.startswith(namespace):
                    return self._receipt(request, "REJECTED_PROTECTED_NAMESPACE", f"Mutation command '{request.command_type.value}' forbidden on protected namespace '{namespace}'")
        return self._receipt(request, "EXECUTED")
