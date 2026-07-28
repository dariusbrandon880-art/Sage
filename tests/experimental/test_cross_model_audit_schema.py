"""SAGE Cross-Model Audit Payload Schema validation and integration test suite."""

import pytest
import os
import ast
import re
from pathlib import Path
from datetime import datetime, timezone

from sage.experimental.act import CrossModelAuditPayloadValidator


def get_valid_payload():
    """Returns a completely valid, conforming CMAPS v1.0 payload dictionary."""
    return {
        "$schema": "https://sage.cos.core/schemas/audit-payload-v1.json",
        "audit_id": "audit_8f9c0e1b2a3d4e5f6a7b8c9d0e1f2a3b",
        "timestamp": "2026-03-30T14:45:30.123456Z",
        "agent_identity": {
            "agent_id": "agent_reliability_monitor_v1",
            "name": "SAGE Reliability Guard",
            "role": "auditor",
            "governance_tier": "experimental"
        },
        "model_provider": {
            "provider": "anthropic",
            "model_name": "claude-3-5-sonnet-v2",
            "temperature": 0.2,
            "max_tokens": 4096,
            "api_version": "2023-06-01"
        },
        "execution_state": {
            "run_id": "run_01j7p8f9q0a1b2c3d4e5f6g7h8",
            "status": "failed",
            "step_counter": 14,
            "started_at": "2026-03-30T14:30:00.000000Z",
            "updated_at": "2026-03-30T14:45:30.123456Z"
        },
        "task_lineage": {
            "session_id": "session_f6b3d4e5",
            "parent_task_id": "task_root_deploy_001",
            "current_task_id": "task_sub_verify_002",
            "subtask_ids": ["task_child_001"]
        },
        "decision_events": [
            {
                "decision_id": "decision_001_approve_credentials",
                "timestamp": "2026-03-30T14:35:10.000000Z",
                "summary": "Verified API credentials.",
                "reasoning": "Reasoning details.",
                "confidence": 0.98
            }
        ],
        "failure_events": [
            {
                "failure_id": "fail_001_boundary_leak",
                "timestamp": "2026-03-30T14:45:28.987654Z",
                "error_type": "AgentBoundaryInterceptionError",
                "message": "Attempted to write to a protected production namespace.",
                "severity": "critical"
            }
        ],
        "recovery_checkpoints": [
            {
                "checkpoint_id": "chk_001_recovery_snapshot",
                "timestamp": "2026-03-30T14:45:30.000000Z",
                "rehydration_token": "rehyd_01j7p8g9r0b1c2d3e4f5g6h7i8",
                "rollback_state_ref": "chk_000_initial_clean_state",
                "requires_human_approval": True
            }
        ],
        "evidence_relationships": [
            {
                "artifact_path": "sage/experimental/act/contracts.py",
                "git_commit": "7553d9b0fb40234008875b534a97ceb653111f82",
                "sha256_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            }
        ],
        "attestation": {
            "nonce": "a7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
            "signature": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
            "signer_identity": "sage_validator_pubkey_01"
        }
    }


def test_validator_with_valid_payload():
    """Verify that a standard conforming payload passes validation cleanly."""
    validator = CrossModelAuditPayloadValidator()
    payload = get_valid_payload()

    result = validator.validate_payload(payload)

    assert result["audit_id"] == "audit_8f9c0e1b2a3d4e5f6a7b8c9d0e1f2a3b"
    assert result["validation_status"] == "SCHEMA_VALIDATED"
    assert result["read_only_assertion"] is True
    assert "validated_at" in result


def test_validator_rejects_non_dictionary():
    """Verify that validator rejects inputs that are not dictionaries."""
    validator = CrossModelAuditPayloadValidator()
    with pytest.raises(ValueError, match="CMAPS Violation: Payload must be a dictionary"):
        validator.validate_payload(["not", "a", "dict"])


def test_validator_missing_top_level_field():
    """Verify missing top-level fields are intercepted and raise ValueError."""
    validator = CrossModelAuditPayloadValidator()
    payload = get_valid_payload()
    del payload["model_provider"]

    with pytest.raises(ValueError, match="CMAPS Violation: Missing required top-level field 'model_provider'"):
        validator.validate_payload(payload)


def test_validator_missing_inner_required_fields():
    """Verify missing fields inside nested objects are caught."""
    validator = CrossModelAuditPayloadValidator()

    # Agent identity nested check
    payload = get_valid_payload()
    del payload["agent_identity"]["governance_tier"]
    with pytest.raises(ValueError, match="CMAPS Violation: Missing 'agent_identity.governance_tier'"):
        validator.validate_payload(payload)

    # Model provider nested check
    payload = get_valid_payload()
    del payload["model_provider"]["temperature"]
    with pytest.raises(ValueError, match="CMAPS Violation: Missing 'model_provider.temperature'"):
        validator.validate_payload(payload)

    # Execution state nested check
    payload = get_valid_payload()
    del payload["execution_state"]["status"]
    with pytest.raises(ValueError, match="CMAPS Violation: Missing 'execution_state.status'"):
        validator.validate_payload(payload)

    # Task lineage nested check
    payload = get_valid_payload()
    del payload["task_lineage"]["subtask_ids"]
    with pytest.raises(ValueError, match="CMAPS Violation: Missing 'task_lineage.subtask_ids'"):
        validator.validate_payload(payload)

    # Attestation nested check
    payload = get_valid_payload()
    del payload["attestation"]["signature"]
    with pytest.raises(ValueError, match="CMAPS Violation: Missing 'attestation.signature'"):
        validator.validate_payload(payload)


def test_validator_invalid_patterns_and_prefixes():
    """Verify format checks reject malformed prefixes/patterns."""
    validator = CrossModelAuditPayloadValidator()

    # audit_id format violation
    payload = get_valid_payload()
    payload["audit_id"] = "aud_123_invalid"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'audit_id'"):
        validator.validate_payload(payload)

    # agent_id format violation
    payload = get_valid_payload()
    payload["agent_identity"]["agent_id"] = "ag_invalid"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'agent_id'"):
        validator.validate_payload(payload)

    # run_id format violation
    payload = get_valid_payload()
    payload["execution_state"]["run_id"] = "run_invalid"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'run_id'"):
        validator.validate_payload(payload)

    # session_id format violation
    payload = get_valid_payload()
    payload["task_lineage"]["session_id"] = "sess_f6b3d4e5"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'session_id'"):
        validator.validate_payload(payload)

    # current_task_id format violation
    payload = get_valid_payload()
    payload["task_lineage"]["current_task_id"] = "task-sub"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'current_task_id'"):
        validator.validate_payload(payload)

    # parent_task_id format violation
    payload = get_valid_payload()
    payload["task_lineage"]["parent_task_id"] = "parent"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'parent_task_id'"):
        validator.validate_payload(payload)

    # decision_id format violation
    payload = get_valid_payload()
    payload["decision_events"][0]["decision_id"] = "dec_invalid"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'decision_id'"):
        validator.validate_payload(payload)

    # failure_id format violation
    payload = get_valid_payload()
    payload["failure_events"][0]["failure_id"] = "fail-leak"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'failure_id'"):
        validator.validate_payload(payload)

    # checkpoint_id format violation
    payload = get_valid_payload()
    payload["recovery_checkpoints"][0]["checkpoint_id"] = "checkpoint_001"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid format for 'checkpoint_id'"):
        validator.validate_payload(payload)


def test_validator_chronological_invariants():
    """Verify chronological timeline rules are strictly enforced."""
    validator = CrossModelAuditPayloadValidator()

    # Timeline mismatch: started_at > updated_at
    payload = get_valid_payload()
    payload["execution_state"]["started_at"] = "2026-03-30T15:00:00Z"
    payload["execution_state"]["updated_at"] = "2026-03-30T14:45:00Z"
    with pytest.raises(ValueError, match="CMAPS Violation: Chronological mismatch. Run 'started_at'"):
        validator.validate_payload(payload)

    # Decision causal mismatch: decision timestamp < run started_at
    payload = get_valid_payload()
    payload["decision_events"][0]["timestamp"] = "2026-03-30T14:20:00Z"
    with pytest.raises(ValueError, match="CMAPS Violation: Chronological mismatch. Decision .* timestamp .* is strictly earlier than run start time"):
        validator.validate_payload(payload)

    # Failure occurred after checkpoint
    payload = get_valid_payload()
    payload["failure_events"][0]["timestamp"] = "2026-03-30T14:46:00Z"
    with pytest.raises(ValueError, match="CMAPS Violation: Chronological mismatch. Intercepted failure .* occurred after checkpoint snapshot"):
        validator.validate_payload(payload)


def test_validator_relational_constraints_and_uniqueness():
    """Verify that relational loops and duplicate IDs are successfully caught."""
    validator = CrossModelAuditPayloadValidator()

    # Relational loop: current_task_id in subtask_ids
    payload = get_valid_payload()
    payload["task_lineage"]["subtask_ids"].append(payload["task_lineage"]["current_task_id"])
    with pytest.raises(ValueError, match="CMAPS Violation: Relational loop detected"):
        validator.validate_payload(payload)

    # Duplicate decision IDs
    payload = get_valid_payload()
    payload["decision_events"].append({
        "decision_id": "decision_001_approve_credentials",
        "timestamp": "2026-03-30T14:40:00Z",
        "summary": "Duplicate decision.",
        "reasoning": "Reason.",
        "confidence": 1.0
    })
    with pytest.raises(ValueError, match="CMAPS Violation: Duplicate decision ID detected"):
        validator.validate_payload(payload)

    # Duplicate checkpoint tokens
    payload = get_valid_payload()
    payload["recovery_checkpoints"].append({
        "checkpoint_id": "chk_002_another",
        "timestamp": "2026-03-30T14:45:30.000000Z",
        "rehydration_token": "rehyd_01j7p8g9r0b1c2d3e4f5g6h7i8",  # Duplicate token
        "requires_human_approval": False
    })
    with pytest.raises(ValueError, match="CMAPS Violation: Duplicate rehydration token detected"):
        validator.validate_payload(payload)


def test_schema_document_exists_and_conforms():
    """Verify that the SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md document exists and has core required parts."""
    root_dir = Path(__file__).parent.parent.parent
    schema_doc = root_dir / "docs" / "SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md"

    assert schema_doc.exists(), "Schema document must exist under docs/"
    content = schema_doc.read_text(encoding="utf-8")

    # Assert necessary topics are described in depth
    assert "SAGE-ACT-CMAPS-1.0" in content
    assert "Schema Purpose" in content
    assert "Field Definitions" in content
    assert "Example Payload" in content
    assert "Lineage Mapping" in content
    assert "Failure & Recovery Mapping" in content
    assert "Validation Requirements" in content
    assert "Future Extension Points" in content


def test_schema_is_indexed_properly():
    """Verify that docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md is listed in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    assert "../docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md" in content
    assert "[State: PROPOSED]" in content
    assert "SAGE Agent Continuity Tree (SAGE-ACT) Multi-Agent Lineage" in content


def test_one_way_import_isolation_enforcement():
    """Verify that the contracts.py module doesn't violate One-Way Import Law."""
    contracts_file = Path(__file__).parent.parent.parent / "sage" / "experimental" / "act" / "contracts.py"
    assert contracts_file.exists(), f"Could not find contracts.py at: {contracts_file}"

    with open(contracts_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(contracts_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("sage.acr"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
                assert not alias.name.startswith("sage.core"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
                assert not alias.name.startswith("sage.agents"), (
                    f"One-Way Import Law Violation: 'contracts.py' directly imports production module '{alias.name}'"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("sage.acr"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )
                assert not node.module.startswith("sage.core"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )
                assert not node.module.startswith("sage.agents"), (
                    f"One-Way Import Law Violation: 'contracts.py' imports from production module '{node.module}'"
                )


def test_validator_model_provider_consistency_mismatch():
    """Verify that inconsistent model/provider pairings raise consistency mismatch errors."""
    validator = CrossModelAuditPayloadValidator()

    # Case 1: Provider 'openai' running non-gpt model
    payload = get_valid_payload()
    payload["model_provider"]["provider"] = "openai"
    payload["model_provider"]["model_name"] = "claude-3-sonnet"
    with pytest.raises(ValueError, match="CMAPS Violation: Model/Provider consistency mismatch. Provider 'openai' cannot run model 'claude-3-sonnet'"):
        validator.validate_payload(payload)

    # Case 2: Provider 'anthropic' running non-claude model
    payload = get_valid_payload()
    payload["model_provider"]["provider"] = "anthropic"
    payload["model_provider"]["model_name"] = "gpt-4o"
    with pytest.raises(ValueError, match="CMAPS Violation: Model/Provider consistency mismatch. Provider 'anthropic' cannot run model 'gpt-4o'"):
        validator.validate_payload(payload)

    # Case 3: Provider 'google' running non-gemini model
    payload = get_valid_payload()
    payload["model_provider"]["provider"] = "google"
    payload["model_provider"]["model_name"] = "claude-3-sonnet"
    with pytest.raises(ValueError, match="CMAPS Violation: Model/Provider consistency mismatch. Provider 'google' cannot run model 'claude-3-sonnet'"):
        validator.validate_payload(payload)


def test_validator_task_hierarchy_self_parenting():
    """Verify that a task with itself listed as parent raises a hierarchy violation error."""
    validator = CrossModelAuditPayloadValidator()

    payload = get_valid_payload()
    payload["task_lineage"]["parent_task_id"] = "task_sub_verify_002"
    payload["task_lineage"]["current_task_id"] = "task_sub_verify_002"

    with pytest.raises(ValueError, match="CMAPS Violation: Task hierarchy violation. parent_task_id cannot equal current_task_id."):
        validator.validate_payload(payload)


def test_validator_decisions_monotonic_ordering():
    """Verify that chronological out-of-order decision events raise a chronological mismatch error."""
    validator = CrossModelAuditPayloadValidator()

    payload = get_valid_payload()
    # Add two decisions where the second occurs BEFORE the first
    payload["decision_events"] = [
        {
            "decision_id": "decision_001_approve_credentials",
            "timestamp": "2026-03-30T14:40:00.000000Z",
            "summary": "Decision 1",
            "reasoning": "Reason 1",
            "confidence": 0.9
        },
        {
            "decision_id": "decision_002_validate_signature",
            "timestamp": "2026-03-30T14:35:00.000000Z",  # strictly earlier
            "summary": "Decision 2",
            "reasoning": "Reason 2",
            "confidence": 0.95
        }
    ]

    with pytest.raises(ValueError, match="CMAPS Violation: Chronological mismatch. Decision 'decision_002_validate_signature' timestamp .* is strictly earlier than previous decision timestamp"):
        validator.validate_payload(payload)


def test_validator_evidence_relationship_validation():
    """Verify evidence structure correctness, required fields, and format checks (git_commit, checksum)."""
    validator = CrossModelAuditPayloadValidator()

    # Case 1: Missing field inside evidence relationships
    payload = get_valid_payload()
    del payload["evidence_relationships"][0]["git_commit"]
    with pytest.raises(ValueError, match="CMAPS Violation: Evidence missing required field 'git_commit'"):
        validator.validate_payload(payload)

    # Case 2: Invalid format for git_commit (must be 40 chars hex)
    payload = get_valid_payload()
    payload["evidence_relationships"][0]["git_commit"] = "short_hash"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid git commit hash format: 'short_hash'"):
        validator.validate_payload(payload)

    # Case 3: Invalid format for sha256_checksum (must be 64 chars hex)
    payload = get_valid_payload()
    payload["evidence_relationships"][0]["sha256_checksum"] = "invalid_sha"
    with pytest.raises(ValueError, match="CMAPS Violation: Invalid sha256 checksum format: 'invalid_sha'"):
        validator.validate_payload(payload)


def test_validator_recovery_state_integrity():
    """Verify that transitioning to recovered status without a failure and checkpoint context is blocked."""
    validator = CrossModelAuditPayloadValidator()

    # Case 1: recovered state but failure_events list is empty
    payload = get_valid_payload()
    payload["execution_state"]["status"] = "recovered"
    payload["failure_events"] = []
    with pytest.raises(ValueError, match="CMAPS Violation: Recovery state transition integrity violation. Status 'recovered' requires at least one failure_event."):
        validator.validate_payload(payload)

    # Case 2: recovered state but recovery_checkpoints list is empty
    payload = get_valid_payload()
    payload["execution_state"]["status"] = "recovered"
    payload["recovery_checkpoints"] = []
    with pytest.raises(ValueError, match="CMAPS Violation: Recovery state transition integrity violation. Status 'recovered' requires at least one recovery_checkpoint."):
        validator.validate_payload(payload)


def test_stabilization_report_exists_and_conforms():
    """Verify that SAGE-CROSS-MODEL-AUDIT-PAYLOAD-STABILIZATION-REPORT.md exists and contains stabilization findings."""
    root_dir = Path(__file__).parent.parent.parent
    report_file = root_dir / "docs" / "SAGE-CROSS-MODEL-AUDIT-PAYLOAD-STABILIZATION-REPORT.md"

    assert report_file.exists(), "Stabilization report must exist under docs/"
    content = report_file.read_text(encoding="utf-8")

    # Assert necessary topics are described in depth
    assert "SAGE-ACT-CMAPS-SR-1.0" in content
    assert "Validation Summary" in content
    assert "Architectural Findings" in content
    assert "Compatibility Assessment" in content
    assert "Evidence Lifecycle Review" in content
    assert "Minimality Review" in content
    assert "Risks Identified & Mitigations" in content
    assert "RECOMMENDED LIFECYCLE STATUS" in content
    assert "ARCHITECTURALLY STABILIZED" in content


def test_stabilization_report_is_indexed_properly():
    """Verify that SAGE-CROSS-MODEL-AUDIT-PAYLOAD-STABILIZATION-REPORT.md is listed as PROPOSED in INDEX.md."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    assert "../docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-STABILIZATION-REPORT.md" in content
    assert "[State: PROPOSED]" in content
    assert "SAGE Agent Continuity Tree (SAGE-ACT) Multi-Agent Lineage" in content


def test_controlled_usage_report_exists_and_conforms():
    """Verify that SAGE-CMAPS-V1-CONTROLLED-USAGE-VALIDATION-REPORT.md exists and contains findings."""
    root_dir = Path(__file__).parent.parent.parent
    report_file = root_dir / "docs" / "SAGE-CMAPS-V1-CONTROLLED-USAGE-VALIDATION-REPORT.md"

    assert report_file.exists(), "Usage validation report must exist under docs/"
    content = report_file.read_text(encoding="utf-8")

    # Assert necessary topics are described in depth
    assert "SAGE-ACT-CMAPS-CUVR-1.0" in content
    assert "Validation Summary" in content
    assert "Validation Scenarios Executed" in content
    assert "Workflow Coverage Analysis" in content
    assert "Cross-Model Neutrality Assessment" in content
    assert "Evidence Usefulness Evaluation" in content
    assert "Minimality Review" in content
    assert "Limitations & Compatibility Observations" in content
    assert "Remain ARCHITECTURALLY STABILIZED RECOMMENDATION" in content


def test_controlled_usage_report_is_indexed_properly():
    """Verify that SAGE-CMAPS-V1-CONTROLLED-USAGE-VALIDATION-REPORT.md is listed as PROPOSED in INDEX.md."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    assert "../docs/SAGE-CMAPS-V1-CONTROLLED-USAGE-VALIDATION-REPORT.md" in content
    assert "[State: PROPOSED]" in content
    assert "SAGE Agent Continuity Tree (SAGE-ACT) Multi-Agent Lineage" in content


def test_synchronization_report_exists_and_conforms():
    """Verify that SAGE-CONTINUITY-SYNCHRONIZATION-REPORT.md exists and contains synchronization details."""
    root_dir = Path(__file__).parent.parent.parent
    report_file = root_dir / "docs" / "SAGE-CONTINUITY-SYNCHRONIZATION-REPORT.md"

    assert report_file.exists(), "Synchronization report must exist under docs/"
    content = report_file.read_text(encoding="utf-8")

    # Assert necessary topics are described in depth
    assert "SAGE-ACT-CMAPS-CSR-1.0" in content
    assert "Validation Summary & Purpose" in content
    assert "SAGE Strategic Positioning" in content
    assert "Core Reliability & Organizational Patterns" in content
    assert "Governance Principles & Lifecycles" in content
    assert "Protection Framework Posture" in content
    assert "CMAPS Lifecycle Status Verification" in content
    assert "Repository Boundary Rules" in content
    assert "Boundary Audit & Operational Findings" in content


def test_synchronization_report_is_indexed_properly():
    """Verify that SAGE-CONTINUITY-SYNCHRONIZATION-REPORT.md is listed as PROPOSED in INDEX.md."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    assert "../docs/SAGE-CONTINUITY-SYNCHRONIZATION-REPORT.md" in content
    assert "[State: PROPOSED]" in content
    assert "SAGE Agent Continuity Tree (SAGE-ACT) Multi-Agent Lineage" in content
