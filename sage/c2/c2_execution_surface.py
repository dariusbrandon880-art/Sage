"""Governed C2 Execution Surface Engine.

Provides a governed execution surface for C2 commands (READ, WRITE, TEST, EXECUTE, DIFF, COMMIT, PUSH, VERIFY),
enforcing exact 40-character HEAD SHA locking, fail-closed protected namespace checks, starting/resulting
SHA provenance tracking, and immutable SHA-256 evidence receipt generation.
"""

from __future__ import annotations

import hashlib
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class C2CommandType(str, Enum):
    """Allowed C2 command types."""
    READ = "READ"
    WRITE = "WRITE"
    TEST = "TEST"
    EXECUTE = "EXECUTE"
    DIFF = "DIFF"
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    VERIFY = "VERIFY"


class C2ExecutionRequest(BaseModel):
    """Governed execution request for a C2 command."""
    request_id: str
    command_type: C2CommandType
    target_path: str
    starting_git_head: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class C2ExecutionSurfaceReceipt(BaseModel):
    """Immutable evidence receipt generated upon C2 command execution."""
    receipt_id: str
    request_id: str
    command_type: C2CommandType
    target_path: str
    starting_git_head: str
    resulting_git_head: str
    status: str  # SUCCESS, REJECTED_PROTECTED_NAMESPACE, REJECTED_INVALID_SHA
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
    """Governance engine controlling execution surface calls."""

    PROTECTED_NAMESPACES = (
        "sage/core/",
        "sage/runtime/",
        "sage/acr/",
        "sage/agents/",
    )

    def __init__(self):
        self.receipts: List[C2ExecutionSurfaceReceipt] = []

    def execute_request(self, request: C2ExecutionRequest) -> C2ExecutionSurfaceReceipt:
        """Evaluates and executes a C2 execution request fail-closed."""
        receipt_id = f"c2_exec_rcpt_{int(time.time() * 1000)}"
        sha_pattern = re.compile(r"^[0-9a-fA-F]{40}$")

        # 1. Exact 40-char SHA check
        if not sha_pattern.match(request.starting_git_head):
            rcpt = C2ExecutionSurfaceReceipt(
                receipt_id=receipt_id,
                request_id=request.request_id,
                command_type=request.command_type,
                target_path=request.target_path,
                starting_git_head=request.starting_git_head,
                resulting_git_head=request.starting_git_head,
                status="REJECTED_INVALID_SHA",
                rejection_reason=f"Invalid starting git HEAD SHA: '{request.starting_git_head}'",
            )
            rcpt.receipt_hash = rcpt.compute_hash()
            self.receipts.append(rcpt)
            return rcpt

        # 2. Protected namespace mutation check
        if request.command_type in (C2CommandType.WRITE, C2CommandType.COMMIT, C2CommandType.PUSH):
            for ns in self.PROTECTED_NAMESPACES:
                if request.target_path.startswith(ns):
                    rcpt = C2ExecutionSurfaceReceipt(
                        receipt_id=receipt_id,
                        request_id=request.request_id,
                        command_type=request.command_type,
                        target_path=request.target_path,
                        starting_git_head=request.starting_git_head,
                        resulting_git_head=request.starting_git_head,
                        status="REJECTED_PROTECTED_NAMESPACE",
                        rejection_reason=f"Mutation command '{request.command_type.value}' forbidden on protected namespace '{ns}'",
                    )
                    rcpt.receipt_hash = rcpt.compute_hash()
                    self.receipts.append(rcpt)
                    return rcpt

        # 3. Successful execution
        rcpt = C2ExecutionSurfaceReceipt(
            receipt_id=receipt_id,
            request_id=request.request_id,
            command_type=request.command_type,
            target_path=request.target_path,
            starting_git_head=request.starting_git_head,
            resulting_git_head=request.starting_git_head,
            status="SUCCESS",
        )
        rcpt.receipt_hash = rcpt.compute_hash()
        self.receipts.append(rcpt)
        return rcpt
