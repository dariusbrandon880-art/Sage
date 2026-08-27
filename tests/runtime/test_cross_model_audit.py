import pytest

from sage.runtime.cross_model_audit import (
    CrossModelAuditValidationError,
    CrossModelAuditValidator,
    sha256_text,
)


HEAD = "0123456789abcdef0123456789abcdef01234567"


def valid_payload():
    return {
        "$schema": "https://sage.cos.core/schemas/audit-payload-v1.json",
        "audit_id": "audit_0123456789abcdef0123456789abcdef",
        "timestamp": "2026-08-27T17:00:00Z",
        "agent_identity": {
            "agent_id": "agent_gemini_recon_v1",
            "name": "Gemini Recon",
            "role": "reconnaissance",
            "governance_tier": "experimental",
        },
        "model_provider": {"provider": "google", "model_name": "gemini", "temperature": 0.2},
        "execution_state": {
            "run_id": "run_0123456789abcdef0123",
            "status": "completed",
            "step_counter": 4,
            "started_at": "2026-08-27T16:59:00Z",
            "updated_at": "2026-08-27T17:00:00Z",
        },
        "task_lineage": {
            "session_id": "session_01234567",
            "current_task_id": "task_recon_001",
            "subtask_ids": [],
        },
        "decision_events": [],
        "failure_events": [],
        "recovery_checkpoints": [],
        "evidence_relationships": [
            {"artifact_path": "evidence/recon.json", "git_commit": HEAD, "sha256_checksum": sha256_text("evidence")}
        ],
        "attestation": {"nonce": "nonce-1", "signature": "sig-1", "signer_identity": "sage-validator"},
    }


def test_valid_payload_is_accepted():
    result = CrossModelAuditValidator.validate(valid_payload(), expected_git_sha=HEAD)
    assert result["validated"] is True
    assert result["git_sha"] == HEAD


def test_missing_top_level_field_fails_closed():
    payload = valid_payload()
    payload.pop("attestation")
    with pytest.raises(CrossModelAuditValidationError, match="missing required fields"):
        CrossModelAuditValidator.validate(payload, expected_git_sha=HEAD)


def test_wrong_execution_head_fails_closed():
    payload = valid_payload()
    payload["evidence_relationships"][0]["git_commit"] = "f" * 40
    with pytest.raises(CrossModelAuditValidationError, match="canonical execution HEAD"):
        CrossModelAuditValidator.validate(payload, expected_git_sha=HEAD)


def test_external_authority_claim_fails_closed():
    payload = valid_payload()
    payload["agent_identity"]["write_authority"] = True
    with pytest.raises(CrossModelAuditValidationError, match="write_authority"):
        CrossModelAuditValidator.validate(payload, expected_git_sha=HEAD)


def test_invalid_checksum_fails_closed():
    payload = valid_payload()
    payload["evidence_relationships"][0]["sha256_checksum"] = "bad"
    with pytest.raises(CrossModelAuditValidationError, match="sha256_checksum"):
        CrossModelAuditValidator.validate(payload, expected_git_sha=HEAD)
