"""SAGE Fleet Evolution Intelligence Layer.

Measures SAGE execution capability growth and efficiency over time without modifying C2 governance,
airspace state, or wave architecture.

Governance Laws:
- Read-Only Signal: Evolution metrics never award XP, promote CQL/SQL, or expand fleet capacity.
- Quality Over Quantity: High receipt counts with incomplete evidence trigger growth index penalties.
- Stale Commitment Rejection: Mixed or stale commit provenance degrades growth signal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import subprocess
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvolutionCategory(str, Enum):
    """Evolution Metric Categories."""
    FLIGHT_QUALITY = "FLIGHT_QUALITY"
    RECONVERGENCE_EFFICIENCY = "RECONVERGENCE_EFFICIENCY"
    EVIDENCE_INTEGRITY = "EVIDENCE_INTEGRITY"
    REUSABLE_PATTERNS = "REUSABLE_PATTERNS"
    REGRESSION_RESISTANCE = "REGRESSION_RESISTANCE"


class EvolutionMetric(BaseModel):
    """Structured metric measuring a specific vector of execution growth."""
    metric_name: str
    category: EvolutionCategory
    score: float = Field(ge=0.0, le=1.0)
    evidence_refs: List[str] = Field(default_factory=list)
    rationale: str


class EvolutionReceipt(BaseModel):
    """Immutable evidence receipt capturing a point-in-time capability growth signal."""
    receipt_id: str
    commit_sha: str
    metrics: Dict[str, EvolutionMetric]
    growth_index: float = Field(ge=0.0, le=1.0)
    growth_signal: str  # ACCELERATING, STABLE, DEGRADED, BLOCKED
    provenance_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class OrganismGrowthReceipt(BaseModel):
    """Cryptographic evidence receipt capturing multi-vector organism capability growth."""
    receipt_id: str
    commit_sha: str
    velocity_score: float = Field(ge=0.0, le=1.0)
    prediction_accuracy_score: float = Field(ge=0.0, le=1.0)
    wave_completion_rate: float = Field(ge=0.0, le=1.0)
    anti_drift_compliance_score: float = Field(ge=0.0, le=1.0)
    compound_growth_index: float = Field(ge=0.0, le=1.0)
    growth_verdict: str  # ACCELERATING, STABLE, DEGRADED, BLOCKED
    provenance_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def _get_current_commit_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def compute_evolution_provenance_hash(
    commit_sha: str,
    growth_signal: str,
    growth_index: float,
    metrics: Dict[str, EvolutionMetric],
) -> str:
    material = "|".join(
        f"{m_name}:{m.category.value}:{m.score:.4f}"
        for m_name, m in sorted(metrics.items())
    )
    payload = f"{commit_sha}:{growth_signal}:{growth_index:.4f}:{material}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_receipt_valid(receipt: Dict[str, Any]) -> bool:
    if not isinstance(receipt, dict):
        return False
    valid_statuses = {"PASS", "READY", "VALIDATED"}
    keys_to_check = [
        "status",
        "wave_verdict",
        "bridge_verdict",
        "router_verdict",
        "fleet_verdict",
        "overall_status",
    ]
    return any(receipt.get(key) in valid_statuses for key in keys_to_check)


class FleetEvolutionIntelligence:
    """Evaluates execution capability growth signals from historical receipts in a read-only manner."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    def evaluate_growth_signal(
        self,
        historical_receipts: List[Dict[str, Any]],
        *,
        test_pass_rate: float = 1.0,
        protected_path_violations: int = 0,
    ) -> EvolutionReceipt:
        """Analyze historical evidence receipts to derive a growth signal and evolution receipt."""
        metrics: Dict[str, EvolutionMetric] = {}

        # 1. Protected Path Violations
        if protected_path_violations > 0:
            growth_signal = "BLOCKED"
            growth_index = 0.0
            metrics["protected_boundary"] = EvolutionMetric(
                metric_name="protected_boundary",
                category=EvolutionCategory.REGRESSION_RESISTANCE,
                score=0.0,
                evidence_refs=[],
                rationale=f"BLOCKED: {protected_path_violations} protected path violation(s) detected.",
            )
            provenance_hash = compute_evolution_provenance_hash(
                self.commit_sha, growth_signal, growth_index, metrics
            )
            return EvolutionReceipt(
                receipt_id=f"evol_rcpt_{hashlib.sha256(provenance_hash.encode()).hexdigest()[:12]}",
                commit_sha=self.commit_sha,
                metrics=metrics,
                growth_index=growth_index,
                growth_signal=growth_signal,
                provenance_hash=provenance_hash,
            )

        # 2. Analyze Receipts
        total_receipts = len(historical_receipts)
        if total_receipts == 0:
            growth_signal = "STABLE"
            growth_index = 0.5
            metrics["baseline_activity"] = EvolutionMetric(
                metric_name="baseline_activity",
                category=EvolutionCategory.FLIGHT_QUALITY,
                score=0.5,
                evidence_refs=[],
                rationale="STABLE: No historical receipts present; baseline score applied.",
            )
            provenance_hash = compute_evolution_provenance_hash(
                self.commit_sha, growth_signal, growth_index, metrics
            )
            return EvolutionReceipt(
                receipt_id=f"evol_rcpt_{hashlib.sha256(provenance_hash.encode()).hexdigest()[:12]}",
                commit_sha=self.commit_sha,
                metrics=metrics,
                growth_index=growth_index,
                growth_signal=growth_signal,
                provenance_hash=provenance_hash,
            )

        valid_receipts = [r for r in historical_receipts if _is_receipt_valid(r)]
        valid_ratio = len(valid_receipts) / total_receipts

        # Check for commit SHA alignment (if commit_sha is explicitly declared in receipt)
        stale_commits = [
            r.get("commit_sha") for r in historical_receipts
            if isinstance(r, dict) and r.get("commit_sha") and r.get("commit_sha") != self.commit_sha
        ]

        metrics["flight_quality"] = EvolutionMetric(
            metric_name="flight_quality",
            category=EvolutionCategory.FLIGHT_QUALITY,
            score=round(valid_ratio, 4),
            evidence_refs=[str(r.get("receipt_id", r.get("commit_sha", "ref"))) for r in valid_receipts[:5]],
            rationale=f"Flight quality ratio is {valid_ratio * 100:.1f}% across {total_receipts} receipts.",
        )

        metrics["regression_resistance"] = EvolutionMetric(
            metric_name="regression_resistance",
            category=EvolutionCategory.REGRESSION_RESISTANCE,
            score=round(test_pass_rate, 4),
            evidence_refs=["platform_test_suite"],
            rationale=f"Platform test pass rate is {test_pass_rate * 100:.1f}%.",
        )

        # Quantity over quality penalty check
        quality_penalty = 0.0
        if total_receipts > 3 and valid_ratio < 0.8:
            quality_penalty = 0.2

        raw_index = (valid_ratio * 0.5) + (test_pass_rate * 0.5) - quality_penalty
        if stale_commits:
            raw_index -= 0.1

        growth_index = round(min(1.0, max(0.0, raw_index)), 4)

        if test_pass_rate < 1.0 or valid_ratio < 0.7 or len(stale_commits) > 0:
            growth_signal = "DEGRADED"
        elif growth_index >= 0.8:
            growth_signal = "ACCELERATING"
        else:
            growth_signal = "STABLE"

        provenance_hash = compute_evolution_provenance_hash(
            self.commit_sha, growth_signal, growth_index, metrics
        )

        return EvolutionReceipt(
            receipt_id=f"evol_rcpt_{hashlib.sha256(provenance_hash.encode()).hexdigest()[:12]}",
            commit_sha=self.commit_sha,
            metrics=metrics,
            growth_index=growth_index,
            growth_signal=growth_signal,
            provenance_hash=provenance_hash,
        )

    def evaluate_organism_growth_rate(
        self,
        *,
        velocity_score: float = 1.0,
        prediction_accuracy_score: float = 1.0,
        wave_completion_rate: float = 1.0,
        anti_drift_compliance_score: float = 1.0,
        protected_path_violations: int = 0,
    ) -> OrganismGrowthReceipt:
        """Calculates a unified compound growth index across multi-session velocity, prediction accuracy, wave completion, and anti-drift compliance."""
        if protected_path_violations > 0:
            growth_verdict = "BLOCKED"
            compound_index = 0.0
        else:
            compound_index = round(
                (velocity_score * 0.25)
                + (prediction_accuracy_score * 0.25)
                + (wave_completion_rate * 0.25)
                + (anti_drift_compliance_score * 0.25),
                4,
            )
            if compound_index >= 0.85:
                growth_verdict = "ACCELERATING"
            elif compound_index >= 0.6:
                growth_verdict = "STABLE"
            else:
                growth_verdict = "DEGRADED"

        payload = f"{self.commit_sha}:{growth_verdict}:{compound_index:.4f}:{velocity_score:.4f}:{prediction_accuracy_score:.4f}:{wave_completion_rate:.4f}:{anti_drift_compliance_score:.4f}".encode("utf-8")
        prov_hash = hashlib.sha256(payload).hexdigest()

        return OrganismGrowthReceipt(
            receipt_id=f"org_growth_{prov_hash[:12]}",
            commit_sha=self.commit_sha,
            velocity_score=velocity_score,
            prediction_accuracy_score=prediction_accuracy_score,
            wave_completion_rate=wave_completion_rate,
            anti_drift_compliance_score=anti_drift_compliance_score,
            compound_growth_index=compound_index,
            growth_verdict=growth_verdict,
            provenance_hash=prov_hash,
        )
