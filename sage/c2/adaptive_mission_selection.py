"""SAGE Adaptive Mission Selection Engine v0.1.

Synthesizes inbound candidate proposals from failure intelligence, capability lineage,
mission intake, and dependency analysis to produce ranked CandidateDecisionPacket records.
Enforces strict fail-closed authorization boundaries (is_authorized = False by default)
and falsification filtering against protected core namespaces.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Sequence
from pydantic import BaseModel, Field

PROTECTED_NAMESPACES = (
    "sage/core/",
    "sage/runtime/",
    "sage/acr/",
    "sage/agents/",
)


class CandidateDecisionPacket(BaseModel):
    """Schema for a C2 candidate mission decision packet."""

    candidate_id: str
    description: str
    evidence_refs: list[str] = Field(default_factory=list)
    failure_context: dict[str, Any] = Field(default_factory=dict)
    dependency_context: dict[str, Any] = Field(default_factory=dict)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    protected_path_intersections: list[str] = Field(default_factory=list)
    verification_requirements: list[str] = Field(default_factory=list)
    falsification_report: dict[str, Any] = Field(default_factory=dict)
    is_authorized: bool = Field(default=False)
    timestamp: float = Field(default_factory=time.time)

    def digest(self) -> str:
        payload = {
            "candidate_id": self.candidate_id,
            "description": self.description,
            "evidence_refs": sorted(self.evidence_refs),
            "risk_score": self.risk_score,
            "protected_path_intersections": sorted(self.protected_path_intersections),
            "verification_requirements": sorted(self.verification_requirements),
            "is_authorized": self.is_authorized,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AdaptiveMissionSelectionEngine:
    """Engine normalizing, scoring, and generating CandidateDecisionPacket records."""

    def __init__(self, protected_namespaces: Sequence[str] = PROTECTED_NAMESPACES):
        self.protected_namespaces = tuple(protected_namespaces)

    def evaluate_candidate(self, raw_candidate: dict[str, Any]) -> CandidateDecisionPacket:
        """Evaluate a single raw candidate dictionary and produce a CandidateDecisionPacket."""
        candidate_id = str(raw_candidate.get("candidate_id") or raw_candidate.get("name") or "").strip()
        description = str(raw_candidate.get("description") or raw_candidate.get("objective") or "").strip()

        if not candidate_id or not description:
            raise ValueError("Candidate requires non-empty candidate_id and description")

        evidence_refs = [str(r).strip() for r in raw_candidate.get("evidence_refs", []) if str(r).strip()]
        affected_paths = [str(p).strip() for p in raw_candidate.get("affected_paths", []) if str(p).strip()]
        verification_reqs = [str(v).strip() for v in raw_candidate.get("verification_requirements", []) if str(v).strip()]

        # Falsification check 1: Intersections with protected namespaces
        intersections = []
        for path in affected_paths:
            for protected in self.protected_namespaces:
                if path.startswith(protected) or protected in path:
                    intersections.append(path)
                    break

        intersections = sorted(list(set(intersections)))

        # Risk scoring logic:
        # Base risk: 10.0
        # +30.0 if protected path intersection exists
        # +20.0 if verification requirements are missing
        # +15.0 if failure context indicates recurring defect
        risk_score = 10.0
        if intersections:
            risk_score += 30.0
        if not verification_reqs:
            risk_score += 20.0

        failure_ctx = raw_candidate.get("failure_context", {})
        if failure_ctx.get("recurring"):
            risk_score += 15.0

        risk_score = min(100.0, risk_score)

        # Falsification report
        passed_falsification = True
        reasons = []

        if intersections:
            passed_falsification = False
            reasons.append(f"Protected path intersection detected: {intersections}")

        if not verification_reqs:
            passed_falsification = False
            reasons.append("Missing required verification specifications")

        falsification_report = {
            "passed": passed_falsification,
            "reasons": reasons,
            "checked_paths": affected_paths,
            "intersections": intersections,
        }

        # ALWAYS default to is_authorized = False (fail-closed posture)
        return CandidateDecisionPacket(
            candidate_id=candidate_id,
            description=description,
            evidence_refs=evidence_refs,
            failure_context=failure_ctx,
            dependency_context=raw_candidate.get("dependency_context", {}),
            risk_score=risk_score,
            protected_path_intersections=intersections,
            verification_requirements=verification_reqs,
            falsification_report=falsification_report,
            is_authorized=False,
        )

    def rank_candidates(self, raw_candidates: Sequence[dict[str, Any]]) -> list[CandidateDecisionPacket]:
        """Process and rank candidates deterministically by falsification status and risk score."""
        packets = []
        for raw in raw_candidates:
            packet = self.evaluate_candidate(raw)
            packets.append(packet)

        # Sort key:
        # 1. Passed falsification first (bool: True before False -> -int(passed))
        # 2. Risk score ascending (lower risk first)
        # 3. Candidate ID lexicographically for determinism
        def sort_key(p: CandidateDecisionPacket) -> tuple[int, float, str]:
            passed = p.falsification_report.get("passed", False)
            return (-int(passed), p.risk_score, p.candidate_id)

        return sorted(packets, key=sort_key)
