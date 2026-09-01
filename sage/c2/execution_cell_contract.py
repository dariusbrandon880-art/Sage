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
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

SHA256_RE = re.compile(r"^[0-9a-f]{40}$")
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
        if not SHA256_RE.fullmatch(value):
            raise ValueError("CANONICAL_HEAD_SHA_MUST_BE_EXACTLY_40_LOWERCASE_HEX_CHARS")
        return value

    @field_validator("wagering_executed")
    @classmethod
    def reject_wagering(cls, value: bool) -> bool:
        if value:
            raise ValueError("EXECUTION_CELL_SHADOW_BOUNDARY_VIOLATION")
        return value

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(exclude={"signature"}, mode="json")
        return payload

    def compute_package_hash(self) -> str:
        """Compute cryptographic SHA-256 hash over canonical mission payload."""
        import json
        serialized = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

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
        return any(path == allowed or path.startswith(allowed.rstrip("/") + "/") for allowed in self.allowed_paths)


class ExecutionAttestation(BaseModel):
    contract_version: str = "1.0.0"
    mission_id: str
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
    mission_package_hash: Optional[str] = None
    attestation_digest: Optional[str] = None

    @field_validator("executed_head_sha", "produced_head_sha")
    @classmethod
    def validate_attestation_sha(cls, value: str) -> str:
        if not SHA256_RE.fullmatch(value):
            raise ValueError("ATTESTATION_SHA_MUST_BE_EXACTLY_40_LOWERCASE_HEX_CHARS")
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

    def compute_digest(self) -> str:
        """Compute cryptographic SHA-256 digest over complete execution attestation payload."""
        import json
        payload = {
            "contract_version": self.contract_version,
            "mission_id": self.mission_id,
            "substrate": self.substrate,
            "status": self.status,
            "exit_code": self.exit_code,
            "executed_head_sha": self.executed_head_sha,
            "produced_head_sha": self.produced_head_sha,
            "receipt_path": self.receipt_path,
            "exact_head_verified": self.exact_head_verified,
            "test_pass_rate": self.test_pass_rate,
            "collision_detected": self.collision_detected,
            "mission_package_hash": self.mission_package_hash or "",
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Return True if stored attestation_digest matches current computed digest."""
        if not self.attestation_digest:
            return False
        return self.attestation_digest == self.compute_digest()

    def verify_mission_binding(self, mission: MissionPackage) -> bool:
        """Verify attestation is bound to exact authorized mission package, ID, and head SHA."""
        if not mission or not self.acceptance_eligible():
            return False
        if self.mission_id != mission.mission_id:
            return False
        if self.executed_head_sha != mission.canonical_head_sha:
            return False
        if self.mission_package_hash:
            if self.mission_package_hash != mission.compute_package_hash():
                return False
        return True

    def acceptance_eligible(self) -> bool:
        """Return true only when the attestation itself satisfies hard gates."""
        return (
            self.status == "PASS"
            and self.exit_code == 0
            and self.exact_head_verified
            and self.test_pass_rate == 1.0
            and not self.collision_detected
            and not self.wagering_executed
        )
