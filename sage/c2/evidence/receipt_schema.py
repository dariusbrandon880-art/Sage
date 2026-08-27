"""SLSA-aligned, SHA/run/job/digest-bound SAGE evidence receipts.

This module does not claim SLSA Build Level 3 compliance. It provides
SLSA-aligned provenance controls that can be used as one component of a
larger trusted build system.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time
from typing import Any, Dict


HEX_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class ProvenanceTuple:
    """Identity of the execution that produced a receipt."""

    wave_id: str
    flight_id: str
    executed_head: str
    base_commit: str
    workflow_run_id: str
    job_id: str
    artifact_digest: str

    def validate(self) -> None:
        if not self.wave_id or not self.flight_id:
            raise ValueError("wave_id and flight_id must be non-empty")
        if not HEX_SHA40.fullmatch(self.executed_head):
            raise ValueError("executed_head must be a 40-character commit SHA")
        if not HEX_SHA40.fullmatch(self.base_commit):
            raise ValueError("base_commit must be a 40-character commit SHA")
        if not self.workflow_run_id or not self.job_id:
            raise ValueError("workflow_run_id and job_id must be non-empty")
        if not SHA256_DIGEST.fullmatch(self.artifact_digest):
            raise ValueError("artifact_digest must use sha256:<64 hex characters>")

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrictEvidenceReceipt:
    """Immutable logical receipt whose authority is determined by exact context equality."""

    receipt_id: str
    provenance: ProvenanceTuple
    passed: bool
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.receipt_id:
            raise ValueError("receipt_id must be non-empty")
        self.provenance.validate()
        if not isinstance(self.passed, bool):
            raise ValueError("passed must be boolean")

    def verify_against_context(
        self,
        expected_provenance: ProvenanceTuple,
        independently_observed_digest: str,
    ) -> bool:
        """Require exact tuple equality plus independently observed artifact digest."""
        try:
            self.validate()
            expected_provenance.validate()
        except ValueError:
            return False
        if not SHA256_DIGEST.fullmatch(independently_observed_digest):
            return False
        return (
            self.passed
            and self.provenance == expected_provenance
            and self.provenance.artifact_digest == independently_observed_digest
        )

    def canonical_bytes(self) -> bytes:
        payload = {
            "receipt_id": self.receipt_id,
            "provenance": self.provenance.as_dict(),
            "passed": self.passed,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def receipt_digest(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_bytes()).hexdigest()
