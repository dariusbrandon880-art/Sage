"""Cryptographically bound AIET validation receipts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


def _get_git_head_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return "0000000000000000000000000000000000000000"


class AIETValidationReceipt(BaseModel):
    """Immutable evidence record for one AIET validation flight."""

    receipt_id: str
    mission_id: str
    trials_count: int = Field(ge=0)
    scenarios_evaluated: List[str]
    perturbations_injected: List[str]
    baseline_technique_id: str
    candidate_technique_id: str
    adaptation_gain: float = Field(ge=0.0)
    recovery_rate: float = Field(ge=0.0, le=1.0)
    transfer_efficiency: float = Field(ge=0.0, le=1.0)
    resilience_score: float = Field(ge=0.0, le=1.0)
    evolution_decision: str
    overall_verdict: str
    isolation_status: str
    initial_state_hash: str
    scenario_hash: str
    observations: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    failures: List[str] = Field(default_factory=list)
    adaptations: List[str] = Field(default_factory=list)
    constraint_integrity: bool
    verification_integrity: bool
    human_intervention_count: int = Field(ge=0)
    unscripted_discovery: bool
    adaptation_latency_steps: int = Field(ge=0)
    knowledge_delta_retained: List[str] = Field(default_factory=list)
    transfer_result: Dict[str, Any] = Field(default_factory=dict)
    final_state_hash: str
    verdict: str
    evidence_proof_hash: str = ""
    execution_mode: str = "external"
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
            "isolation_status": self.isolation_status,
            "initial_state_hash": self.initial_state_hash,
            "scenario_hash": self.scenario_hash,
            "observations": self.observations,
            "decisions": self.decisions,
            "actions": self.actions,
            "failures": self.failures,
            "adaptations": self.adaptations,
            "constraint_integrity": self.constraint_integrity,
            "verification_integrity": self.verification_integrity,
            "human_intervention_count": self.human_intervention_count,
            "unscripted_discovery": self.unscripted_discovery,
            "adaptation_latency_steps": self.adaptation_latency_steps,
            "knowledge_delta_retained": self.knowledge_delta_retained,
            "transfer_result": self.transfer_result,
            "final_state_hash": self.final_state_hash,
            "verdict": self.verdict,
            "execution_mode": self.execution_mode,
            "fail_closed_reasons": list(self.fail_closed_reasons),
            "git_head_sha": self.git_head_sha,
            "timestamp_utc": self.timestamp_utc,
        }

    def compute_hash(self) -> str:
        payload = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = self.canonical_payload()
        data["evidence_proof_hash"] = self.compute_hash()
        data["receipt_hash"] = data["evidence_proof_hash"]
        return data
