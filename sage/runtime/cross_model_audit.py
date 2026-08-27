"""Fail-closed validation for cross-model execution evidence.

This module validates evidence emitted by external model integrations without
promoting model output to canonical authority. It intentionally does not
capture or require model chain-of-thought.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping


class CrossModelAuditValidationError(ValueError):
    """Raised when an external evidence payload violates the SAGE boundary."""


_REQUIRED_TOP_LEVEL = {
    "$schema",
    "audit_id",
    "timestamp",
    "agent_identity",
    "model_provider",
    "execution_state",
    "task_lineage",
    "decision_events",
    "failure_events",
    "recovery_checkpoints",
    "evidence_relationships",
    "attestation",
}


class CrossModelAuditValidator:
    """Validate CMAPS-shaped evidence against SAGE authority boundaries."""

    CANONICAL_REPOSITORY = "dariusbrandon880-art/Sage"
    PROVIDER_ROLES = {"reconnaissance", "execution", "verification", "adapter"}
    FORBIDDEN_AUTHORITY_KEYS = {
        "canonical_authority",
        "authorization_authority",
        "write_authority",
        "promote_to_production",
        "autonomous_promotion",
    }

    @classmethod
    def validate(
        cls,
        payload: Mapping[str, Any],
        *,
        expected_git_sha: str,
        expected_repository: str = CANONICAL_REPOSITORY,
    ) -> dict[str, Any]:
        """Return a normalized evidence summary or fail closed."""
        if not isinstance(payload, Mapping):
            raise CrossModelAuditValidationError("payload must be a mapping")
        missing = sorted(_REQUIRED_TOP_LEVEL - set(payload))
        if missing:
            raise CrossModelAuditValidationError(f"missing required fields: {', '.join(missing)}")
        if expected_repository != cls.CANONICAL_REPOSITORY:
            raise CrossModelAuditValidationError("unexpected canonical repository")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", expected_git_sha):
            raise CrossModelAuditValidationError("expected_git_sha must be a 40-character SHA-1")

        agent = payload["agent_identity"]
        provider = payload["model_provider"]
        state = payload["execution_state"]
        lineage = payload["task_lineage"]
        evidence = payload["evidence_relationships"]
        attestation = payload["attestation"]

        cls._require_mapping(agent, "agent_identity")
        cls._require_mapping(provider, "model_provider")
        cls._require_mapping(state, "execution_state")
        cls._require_mapping(lineage, "task_lineage")
        cls._require_mapping(attestation, "attestation")
        if not isinstance(evidence, list) or not evidence:
            raise CrossModelAuditValidationError("evidence_relationships must be a non-empty list")

        required_agent = {"agent_id", "name", "role", "governance_tier"}
        required_provider = {"provider", "model_name", "temperature"}
        required_state = {"run_id", "status", "step_counter", "started_at", "updated_at"}
        required_lineage = {"session_id", "current_task_id", "subtask_ids"}
        required_attestation = {"nonce", "signature", "signer_identity"}
        for fields, obj, name in (
            (required_agent, agent, "agent_identity"),
            (required_provider, provider, "model_provider"),
            (required_state, state, "execution_state"),
            (required_lineage, lineage, "task_lineage"),
            (required_attestation, attestation, "attestation"),
        ):
            missing_fields = sorted(fields - set(obj))
            if missing_fields:
                raise CrossModelAuditValidationError(f"{name} missing: {', '.join(missing_fields)}")

        if provider.get("provider") not in {"openai", "google", "anthropic", "ollama", "other"}:
            raise CrossModelAuditValidationError("unsupported model provider")
        if not isinstance(provider["temperature"], (int, float)) or not 0 <= provider["temperature"] <= 2:
            raise CrossModelAuditValidationError("temperature must be between 0 and 2")
        if state["status"] not in {"active", "suspended", "completed", "failed", "recovered"}:
            raise CrossModelAuditValidationError("invalid execution status")
        if not isinstance(state["step_counter"], int) or state["step_counter"] < 0:
            raise CrossModelAuditValidationError("step_counter must be a non-negative integer")
        if agent.get("governance_tier") not in {"canonical", "experimental", "shadow"}:
            raise CrossModelAuditValidationError("invalid governance tier")
        if agent.get("role") not in cls.PROVIDER_ROLES and agent.get("role") != "orchestrator":
            raise CrossModelAuditValidationError("external agent role is not governed")

        for key in cls.FORBIDDEN_AUTHORITY_KEYS:
            if payload.get(key) is True or agent.get(key) is True or provider.get(key) is True:
                raise CrossModelAuditValidationError(f"external model cannot claim {key}")

        for item in evidence:
            cls._require_mapping(item, "evidence_relationship")
            for key in ("artifact_path", "git_commit", "sha256_checksum"):
                if not item.get(key):
                    raise CrossModelAuditValidationError(f"evidence_relationship missing {key}")
            if item["git_commit"] != expected_git_sha:
                raise CrossModelAuditValidationError("evidence git_commit does not match canonical execution HEAD")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", item["sha256_checksum"]):
                raise CrossModelAuditValidationError("sha256_checksum must be 64 hexadecimal characters")

        if not isinstance(payload["decision_events"], list) or not isinstance(payload["failure_events"], list):
            raise CrossModelAuditValidationError("decision_events and failure_events must be lists")
        if not isinstance(payload["recovery_checkpoints"], list):
            raise CrossModelAuditValidationError("recovery_checkpoints must be a list")
        if not attestation["nonce"] or not attestation["signature"] or not attestation["signer_identity"]:
            raise CrossModelAuditValidationError("attestation is incomplete")

        # Return only operational metadata suitable for canonical indexing.
        return {
            "audit_id": payload["audit_id"],
            "run_id": state["run_id"],
            "provider": provider["provider"],
            "model_name": provider["model_name"],
            "governance_tier": agent["governance_tier"],
            "git_sha": expected_git_sha,
            "repository": expected_repository,
            "evidence_count": len(evidence),
            "validated": True,
        }

    @staticmethod
    def _require_mapping(value: Any, name: str) -> None:
        if not isinstance(value, Mapping):
            raise CrossModelAuditValidationError(f"{name} must be a mapping")


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest used by evidence_relationships."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
