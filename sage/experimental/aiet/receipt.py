"""SAGE AIET Validation Receipt.

Defines the cryptographically bound, immutable receipt representing an end-to-end
AIET evaluation flight.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


def _get_git_head_sha() -> str:
    """Helper to resolve current 40-character Git HEAD commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return "0000000000000000000000000000000000000000"


class AIETValidationReceipt(BaseModel):
    """Cryptographically bound receipt for AIET Validation Lab evaluation runs."""

    receipt_id: str
    mission_id: str
    trials_count: int = Field(ge=0)
    scenarios_evaluated: List[str]
    perturbations_injected: List[str]
    baseline_technique_id: str
    candidate_technique_id: str
    adaptation_gain: float
    recovery_rate: float
    transfer_efficiency: float
    resilience_score: float
    evolution_decision: str
    overall_verdict: str
    fail_closed_reasons: Tuple[str, ...] = Field(default_factory=tuple)
    git_head_sha: str = Field(default_factory=_get_git_head_sha)
    timestamp_utc: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "mission_id": self.mission_id,
            "trials_count": self.trials_count,
            "scenarios_evaluated": sorted(self.scenarios_evaluated),
            "perturbations_injected": sorted(self.perturbations_injected),
            "baseline_technique_id": self.baseline_technique_id,
            "candidate_technique_id": self.candidate_technique_id,
            "adaptation_gain": float(self.adaptation_gain),
            "recovery_rate": float(self.recovery_rate),
            "transfer_efficiency": float(self.transfer_efficiency),
            "resilience_score": float(self.resilience_score),
            "evolution_decision": self.evolution_decision,
            "overall_verdict": self.overall_verdict,
            "fail_closed_reasons": list(self.fail_closed_reasons),
            "git_head_sha": self.git_head_sha,
            "timestamp_utc": self.timestamp_utc,
        }

    def compute_hash(self) -> str:
        payload_str = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = self.canonical_payload()
        d["receipt_hash"] = self.compute_hash()
        return d
