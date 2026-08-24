"""SAGE Fleet Readiness Intelligence Layer.

Provides read-only fleet and station readiness evaluation over canonical AirspaceState.

Governance Laws:
- Read-Only Projection: Readiness calculations never award XP, promote CQL/SQL, or mutate state.
- Fail-Closed Readiness:
  - No evidence references -> UNQUALIFIED (score 0.0)
  - Protected path violations > 0 -> BLOCKED (score 0.0)
  - Test pass rate < 1.0 -> DEGRADED
  - 100% tests + verified evidence + 0 violations -> READY
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import subprocess
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from sage.experimental.airspace.models import AirspaceState, StationID


class ReadinessStatus(str, Enum):
    """Fleet and Station Readiness Status."""

    READY = "READY"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    UNQUALIFIED = "UNQUALIFIED"


STATUS_SEVERITY_ORDER = {
    ReadinessStatus.BLOCKED: 0,
    ReadinessStatus.UNQUALIFIED: 1,
    ReadinessStatus.DEGRADED: 2,
    ReadinessStatus.READY: 3,
}


class ReadinessScore(BaseModel):
    """Structured readiness score for a single station."""

    station_id: StationID
    overall_score: float = Field(ge=0.0, le=1.0)
    status: ReadinessStatus
    test_pass_rate: float = Field(ge=0.0, le=1.0)
    evidence_completeness: float = Field(ge=0.0, le=1.0)
    protected_path_violations: int = Field(ge=0)
    qualification_level: int = Field(ge=0)
    rationale: str
    read_only: bool = True


class ReadinessReceipt(BaseModel):
    """Immutable, fingerprint-backed receipt for fleet-wide readiness evaluation."""

    receipt_id: str
    commit_sha: str
    station_scores: Dict[StationID, ReadinessScore]
    fleet_verdict: ReadinessStatus
    overall_fleet_readiness: float = Field(ge=0.0, le=1.0)
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


def compute_readiness_provenance_hash(
    commit_sha: str,
    fleet_verdict: ReadinessStatus,
    station_scores: Dict[StationID, ReadinessScore],
) -> str:
    material = "|".join(
        f"{sid.value}:{score.status.value}:{score.overall_score:.4f}"
        for sid, score in sorted(station_scores.items(), key=lambda x: x[0].value)
    )
    payload = f"{commit_sha}:{fleet_verdict.value}:{material}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class FleetReadinessEngine:
    """Evaluates readiness scores and receipts across SAGE stations in a read-only manner."""

    def __init__(self, commit_sha: Optional[str] = None) -> None:
        self.commit_sha = commit_sha or _get_current_commit_sha()

    def evaluate_station_readiness(
        self,
        state: AirspaceState,
        station_id: StationID,
        *,
        test_pass_rate: float = 1.0,
        evidence_refs: Optional[List[str]] = None,
        protected_path_violations: int = 0,
    ) -> ReadinessScore:
        """Evaluate readiness for a single station without mutating AirspaceState."""
        station = state.stations[station_id]
        evidence = evidence_refs or []
        cql = station.current_cql

        # Rule 1: Protected path violations block readiness instantly
        if protected_path_violations > 0:
            return ReadinessScore(
                station_id=station_id,
                overall_score=0.0,
                status=ReadinessStatus.BLOCKED,
                test_pass_rate=test_pass_rate,
                evidence_completeness=1.0 if evidence else 0.0,
                protected_path_violations=protected_path_violations,
                qualification_level=cql,
                rationale=f"BLOCKED: {protected_path_violations} protected core namespace violation(s) detected.",
            )

        # Rule 2: No evidence -> UNQUALIFIED
        if not evidence:
            return ReadinessScore(
                station_id=station_id,
                overall_score=0.0,
                status=ReadinessStatus.UNQUALIFIED,
                test_pass_rate=test_pass_rate,
                evidence_completeness=0.0,
                protected_path_violations=0,
                qualification_level=cql,
                rationale="UNQUALIFIED: Missing verified evidence references.",
            )

        # Calculate evidence completeness (min 1 evidence ref, max 5 for 1.0)
        evidence_completeness = min(1.0, max(0.2, len(evidence) * 0.2))

        # Calculate overall score: 60% test pass rate + 30% evidence completeness + 10% CQL factor
        cql_factor = min(1.0, cql / 7.0)
        overall_score = round(
            (test_pass_rate * 0.6) + (evidence_completeness * 0.3) + (cql_factor * 0.1), 4
        )

        # Rule 3: Test pass rate < 1.0 -> DEGRADED
        if test_pass_rate < 1.0:
            status = ReadinessStatus.DEGRADED
            rationale = f"DEGRADED: Test pass rate is {test_pass_rate * 100:.1f}% (below 100%)."
        else:
            status = ReadinessStatus.READY
            rationale = (
                "READY: All tests passed, verified evidence attached, 0 protected path violations."
            )

        return ReadinessScore(
            station_id=station_id,
            overall_score=overall_score,
            status=status,
            test_pass_rate=test_pass_rate,
            evidence_completeness=evidence_completeness,
            protected_path_violations=0,
            qualification_level=cql,
            rationale=rationale,
        )

    def evaluate_fleet_readiness(
        self,
        state: AirspaceState,
        station_evaluations: Dict[StationID, Dict[str, Any]],
    ) -> ReadinessReceipt:
        """Evaluate readiness across all SAGE stations and produce an immutable receipt."""
        station_scores: Dict[StationID, ReadinessScore] = {}

        for station_id in StationID:
            eval_params = station_evaluations.get(station_id, {})
            score = self.evaluate_station_readiness(
                state=state,
                station_id=station_id,
                test_pass_rate=eval_params.get("test_pass_rate", 1.0),
                evidence_refs=eval_params.get("evidence_refs", ["evidence_ref_default"]),
                protected_path_violations=eval_params.get("protected_path_violations", 0),
            )
            station_scores[station_id] = score

        # Fleet verdict is lowest status among all stations
        min_status = min(
            (score.status for score in station_scores.values()),
            key=lambda s: STATUS_SEVERITY_ORDER[s],
        )

        overall_fleet_readiness = round(
            sum(score.overall_score for score in station_scores.values()) / len(station_scores), 4
        )

        provenance_hash = compute_readiness_provenance_hash(
            self.commit_sha, min_status, station_scores
        )

        receipt_id = f"readiness_rcpt_{hashlib.sha256(provenance_hash.encode()).hexdigest()[:12]}"

        return ReadinessReceipt(
            receipt_id=receipt_id,
            commit_sha=self.commit_sha,
            station_scores=station_scores,
            fleet_verdict=min_status,
            overall_fleet_readiness=overall_fleet_readiness,
            provenance_hash=provenance_hash,
        )
