"""Fail-closed ingestion of structured Jules execution reports into C2.

Jules reports are observations. This adapter validates provenance and extracts
bounded evidence/state deltas into the existing ExternalSessionPayload seam;
it never authorizes runtime tasks or promotes prose claims to canonical state.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sage.models import ExternalSessionPayload

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class JulesReport(BaseModel):
    """Structured, provenance-bearing Jules completion report."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    git_sha: str
    branch: str = Field(min_length=1)
    status: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    state_deltas: dict[str, Any] = Field(default_factory=dict)
    pr_number: int | None = Field(default=None, ge=1)
    pr_head_sha: str | None = None
    hud_projection: dict[str, Any] | None = None
    hud_update_key: str | None = None

    @field_validator("git_sha", "pr_head_sha")
    @classmethod
    def validate_sha(cls, value: str | None) -> str | None:
        if value is not None and not _SHA40.fullmatch(value):
            raise ValueError("git SHA must be exactly 40 lowercase hexadecimal characters")
        return value


class JulesReportIngestionResult(BaseModel):
    """Receipt-like result returned by the ingestion adapter."""

    model_config = ConfigDict(frozen=True)

    accepted: bool
    report_id: str
    session_id: str
    canonical_git_sha: str
    evidence_digest: str
    rejection_reason: str | None = None


def _evidence_digest(report: JulesReport) -> str:
    material = "\n".join(report.evidence)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def ingest_jules_report(
    runtime: Any,
    report: JulesReport | Mapping[str, Any],
    *,
    canonical_git_sha: str,
) -> JulesReportIngestionResult:
    """Validate lineage and ingest a Jules report as an observed payload.

    The report must match the exact canonical Git HEAD supplied by the caller.
    A PR head SHA, when present, must match that same canonical SHA. Any
    mismatch is rejected before touching runtime memory.
    """

    parsed = report if isinstance(report, JulesReport) else JulesReport.model_validate(report)
    if not _SHA40.fullmatch(canonical_git_sha):
        raise ValueError("canonical_git_sha must be exactly 40 lowercase hexadecimal characters")

    if parsed.git_sha != canonical_git_sha:
        return JulesReportIngestionResult(
            accepted=False,
            report_id=parsed.report_id,
            session_id=parsed.session_id,
            canonical_git_sha=canonical_git_sha,
            evidence_digest=_evidence_digest(parsed),
            rejection_reason="report Git SHA does not match canonical Git HEAD",
        )

    if parsed.pr_head_sha is not None and parsed.pr_head_sha != canonical_git_sha:
        return JulesReportIngestionResult(
            accepted=False,
            report_id=parsed.report_id,
            session_id=parsed.session_id,
            canonical_git_sha=canonical_git_sha,
            evidence_digest=_evidence_digest(parsed),
            rejection_reason="PR head SHA does not match canonical Git HEAD",
        )

    digest = _evidence_digest(parsed)
    payload = ExternalSessionPayload(
        session_id=parsed.session_id,
        objective=parsed.objective,
        task=None,
        memories=[
            {
                "id": parsed.report_id,
                "object_type": "jules_execution_report",
                "content": {
                    "report_id": parsed.report_id,
                    "status": parsed.status,
                    "summary": parsed.summary,
                    "branch": parsed.branch,
                    "canonical_git_sha": canonical_git_sha,
                    "pr_number": parsed.pr_number,
                    "state_deltas": parsed.state_deltas,
                    "evidence": parsed.evidence,
                    "evidence_digest": digest,
                    "hud_projection": parsed.hud_projection,
                    "hud_update_key": parsed.hud_update_key,
                },
                "tags": ["jules", "execution_report", "c2_ingestion", parsed.status.lower()],
                "confidence": "hypothesis",
            }
        ],
        decisions=[],
        metadata={
            "source": "jules",
            "provenance": "exact_git_head",
            "canonical_git_sha": canonical_git_sha,
            "evidence_digest": digest,
            "hud_update_key": parsed.hud_update_key,
        },
    )
    runtime.ingest_session_payload(payload)
    return JulesReportIngestionResult(
        accepted=True,
        report_id=parsed.report_id,
        session_id=parsed.session_id,
        canonical_git_sha=canonical_git_sha,
        evidence_digest=digest,
    )
