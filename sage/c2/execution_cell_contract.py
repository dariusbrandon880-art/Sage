"""SAGE Execution Cell contract primitives.

This module defines the bounded interface between C2 mission control and an
external execution substrate. It validates mission scope and attestation data;
it deliberately does not provide an unrestricted shell or acquire credentials.

The existing Big Jump Wave remains the execution architecture. The Execution
Cell is an actuator contract underneath that architecture.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_SHELL_TOKENS = ("&&", ";", "|", "`", "$(", "\n", "\r")


class FlightAllocation(BaseModel):
    f1_recon: str
    f2_build: str
    f3_test: str
    f4_evidence: str
    f5_converge: str


class CollisionLock(BaseModel):
    resource: str
    lock_acquired: bool


class MissionPackage(BaseModel):
    contract_version: str = "1.0.0"
    mission_id: str
    target_repo: str
    canonical_head_sha: str
    allowed_paths: List[str] = Field(default_factory=list)
    allowed_commands: List[str] = Field(default_factory=list)
    flight_allocation: FlightAllocation
    collision_lock: CollisionLock
    wagering_executed: bool = False
    signature: Optional[str] = None

    @field_validator("canonical_head_sha")
    @classmethod
    def validate_sha(cls, value: str) -> str:
        if not SHA40_RE.fullmatch(value):
            raise ValueError("CANONICAL_HEAD_SHA_MUST_BE_EXACTLY_40_LOWERCASE_HEX_CHARS")
        return value

    @field_validator("wagering_executed")
    @classmethod
    def reject_wagering(cls, value: bool) -> bool:
        if value:
            raise ValueError("EXECUTION_CELL_SHADOW_BOUNDARY_VIOLATION")
        return value

    def canonical_payload(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"signature"}, mode="json")

    def package_digest(self) -> str:
        """Return the canonical digest that an execution attestation must bind."""
        body = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def sign(self, secret: bytes) -> str:
        body = self.model_dump_json(exclude={"signature"}).encode("utf-8")
        return hmac.new(secret, body, hashlib.sha256).hexdigest()

    def verify_signature(self, secret: bytes) -> bool:
        if not self.signature:
            return False
        return hmac.compare_digest(self.signature, self.sign(secret))

    def command_allowed(self, command: str) -> bool:
        """Exact-match allowlist; reject shell composition and unlisted commands."""
        if not command or any(token in command for token in FORBIDDEN_SHELL_TOKENS):
            return False
        return command in self.allowed_commands

    def path_allowed(self, path: str) -> bool:
        """Require an explicit path or directory-prefix allowlist match."""
        if not path or path.startswith("/") or ".." in path.split("/"):
            return False
        return any(
            path == allowed or path.startswith(allowed.rstrip("/") + "/")
            for allowed in self.allowed_paths
        )


class ExecutionAttestation(BaseModel):
    contract_version: str = "1.0.0"
    mission_id: str
    mission_package_digest: Optional[str] = None
    substrate: str
    status: str
    exit_code: int
    executed_head_sha: str
    produced_head_sha: str
    receipt_path: str
    exact_head_verified: bool
    test_pass_rate: float
    collision_detected: bool
    wagering_executed: bool = False
    stderr_digest: Optional[str] = None

    @field_validator("executed_head_sha", "produced_head_sha")
    @classmethod
    def validate_attestation_sha(cls, value: str) -> str:
        if not SHA40_RE.fullmatch(value):
            raise ValueError("ATTESTATION_SHA_MUST_BE_EXACTLY_40_LOWERCASE_HEX_CHARS")
        return value

    @field_validator("mission_package_digest")
    @classmethod
    def validate_mission_digest(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not SHA64_RE.fullmatch(value):
            raise ValueError("MISSION_PACKAGE_DIGEST_MUST_BE_EXACTLY_64_LOWERCASE_HEX_CHARS")
        return value

    @field_validator("test_pass_rate")
    @classmethod
    def validate_pass_rate(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("TEST_PASS_RATE_MUST_BE_BETWEEN_0_AND_1")
        return value

    @field_validator("wagering_executed")
    @classmethod
    def reject_wagering_result(cls, value: bool) -> bool:
        if value:
            raise ValueError("EXECUTION_CELL_SHADOW_BOUNDARY_VIOLATION")
        return value

    def verify_mission_binding(self, mission_package: MissionPackage) -> bool:
        """Require mission identity, exact execution head, and package digest alignment."""
        return (
            self.mission_id == mission_package.mission_id
            and self.mission_package_digest is not None
            and hmac.compare_digest(self.mission_package_digest, mission_package.package_digest())
            and self.executed_head_sha == mission_package.canonical_head_sha
            and self.produced_head_sha == self.executed_head_sha
        )

    def acceptance_eligible(self, mission_package: Optional[MissionPackage] = None) -> bool:
        """Return true only when execution and mission lineage satisfy every hard gate."""
        if mission_package is None or not self.verify_mission_binding(mission_package):
            return False
        return (
            self.status == "PASS"
            and self.exit_code == 0
            and self.exact_head_verified
            and self.test_pass_rate == 1.0
            and not self.collision_detected
            and not self.wagering_executed
        )
