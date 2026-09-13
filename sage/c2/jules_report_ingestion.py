"""Fail-closed ingestion of structured Jules execution reports into C2.

Jules reports are observations. This adapter validates provenance and extracts
bounded evidence/state deltas into the existing ExternalSessionPayload seam;
it never authorizes runtime tasks or promotes prose claims to canonical state.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sage.c2.response_envelope import FieldC2ProjectionEnvelope
from sage.models import ExternalSessionPayload

_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def compute_hud_projection_key(hud_projection: Mapping[str, Any]) -> str:
    """Compute deterministic SHA-256 key for a structured HUD projection."""
    serialized = json.dumps(dict(hud_projection), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


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
    session_lineage: list[str] = Field(default_factory=list)

    @field_validator("git_sha", "pr_head_sha")
    @classmethod
    def validate_sha(cls, value: str | None) -> str | None:
        if value is not None and not _SHA40.fullmatch(value):
            raise ValueError("git SHA must be exactly 40 lowercase hexadecimal characters")
        return value

    @field_validator("hud_update_key")
    @classmethod
    def validate_hud_update_key(cls, value: str | None, info: Any) -> str | None:
        hud_proj = info.data.get("hud_projection")
        if hud_proj is not None:
            expected_key = compute_hud_projection_key(hud_proj)
            if value is not None and value != expected_key:
                raise ValueError("hud_update_key does not match deterministic hud_projection hash")
            return expected_key
        return value


class JulesReportIngestionResult(BaseModel):
    """Receipt-like result returned by the ingestion adapter."""

    model_config = ConfigDict(frozen=True)

    accepted: bool
    report_id: str
    session_id: str
    canonical_git_sha: str
    evidence_digest: str
    hud_update_key: str | None = None
    field_c2_envelope: dict[str, Any] | None = None
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

    calculated_hud_key = (
        compute_hud_projection_key(parsed.hud_projection)
        if parsed.hud_projection is not None
        else parsed.hud_update_key
    )

    envelope = FieldC2ProjectionEnvelope(
        session_id=parsed.session_id,
        report_id=parsed.report_id,
        canonical_git_sha=canonical_git_sha,
        hud_projection=parsed.hud_projection,
        hud_update_key=calculated_hud_key,
        session_lineage=tuple(parsed.session_lineage),
    )

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
                    "hud_update_key": calculated_hud_key,
                    "session_lineage": parsed.session_lineage,
                    "field_c2_envelope": envelope.as_dict(),
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
            "hud_update_key": calculated_hud_key,
            "session_lineage": parsed.session_lineage,
        },
    )
    runtime.ingest_session_payload(payload)
    return JulesReportIngestionResult(
        accepted=True,
        report_id=parsed.report_id,
        session_id=parsed.session_id,
        canonical_git_sha=canonical_git_sha,
        evidence_digest=digest,
        hud_update_key=calculated_hud_key,
        field_c2_envelope=envelope.as_dict(),
    )


def rehydrate_c2_from_jules_report(
    runtime: Any,
    report: JulesReport | Mapping[str, Any],
    *,
    canonical_git_sha: str,
    organism_manager: Any | None = None,
    previous_hud_update_key: str | None = None,
    force_hud: bool = False,
) -> tuple[Any, Any, JulesReportIngestionResult]:
    """Ingest a Jules report and rehydrate the C2 immersion frame from the structured Field-C2 HUD.

    Integrates Field-C2 → Tower-C2 report ingestion with canonical SAGE immersion rehydration.
    Fails closed if the report's Git SHA does not match canonical Git HEAD.
    """
    import importlib
    immersion_rehydrate_mod = importlib.import_module("sage.c2.immersion_rehydration")

    ingestion_result = ingest_jules_report(runtime, report, canonical_git_sha=canonical_git_sha)
    if not ingestion_result.accepted:
        raise ValueError(f"C2 rehydration blocked: Jules report rejected ({ingestion_result.rejection_reason})")

    parsed = report if isinstance(report, JulesReport) else JulesReport.model_validate(report)

    c2_context: dict[str, Any] = {
        "active_objective": parsed.objective,
        "active_task": parsed.summary,
        "canonical_git_sha": canonical_git_sha,
        "session_lineage": parsed.session_lineage,
    }
    if parsed.hud_projection:
        c2_context.update({
            "frontier": parsed.hud_projection.get("frontier"),
            "gate": parsed.hud_projection.get("gate"),
            "flight_id": parsed.hud_projection.get("flight_id"),
        })

    immersion_state, response = immersion_rehydrate_mod.rehydrate_chatgpt_c2_frame(
        runtime,
        session_id=parsed.session_id,
        body=parsed.summary,
        c2_context=c2_context,
        evidence_refs=tuple(parsed.evidence),
        organism_manager=organism_manager,
        force_hud=force_hud,
    )

    if previous_hud_update_key is not None and not force_hud:
        # Re-project response passing down the previous_hud_update_key for continuity evaluation
        chatgpt_immersion_mod = importlib.import_module("sage.c2.chatgpt_immersion")
        response = chatgpt_immersion_mod.project_chatgpt_immersion_response(
            immersion_state,
            body=parsed.summary,
            organism_manager=organism_manager,
            previous_hud_update_key=previous_hud_update_key,
            force_hud=force_hud,
        )

    return immersion_state, response, ingestion_result
