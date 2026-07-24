"""Comprehensive unit and integration tests for SAGE-SKAL deterministic intake boundary."""

import tempfile

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from sage.acr.skal import (
    ArchitectureDecision,
    DeploymentEvent,
    ValidationReport,
    process_incoming_payload,
    promote_skal_payload,
)
from sage.models import ConfidenceLevel
from sage.runtime import SAGERuntime


@pytest.fixture
def temp_runtime():
    """Create a clean SAGE runtime instance using a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(workspace_path=tmpdir)
        runtime.start()
        yield runtime
        runtime.stop()


def test_validation_report_schema_snake_case():
    """Test ValidationReport parses correct snake_case payload."""
    data = {
        "source": "ci-pipeline",
        "timestamp": "2026-03-31T12:00:00Z",
        "commit_identifier": "feat-1234",
        "validation_results": {"tests_passed": True, "coverage": 95.5},
        "evidence_references": ["link-to-logs-1", "link-to-logs-2"],
        "confidence_metadata": {"score": 0.99, "method": "automated-test-suite"},
    }
    report = ValidationReport(**data)
    assert report.source == "ci-pipeline"
    assert report.commit_identifier == "feat-1234"
    assert report.validation_results["coverage"] == 95.5
    assert len(report.evidence_references) == 2
    assert report.confidence_metadata["score"] == 0.99


def test_validation_report_schema_spaced_keys():
    """Test ValidationReport parses correct spaced-key payload."""
    data = {
        "source": "manual-audit",
        "timestamp": "2026-03-31T15:30:00Z",
        "commit identifier": "perf-8888",
        "validation results": {"security_clear": True},
        "evidence references": ["audit-doc-v1"],
        "confidence metadata": {"human_reviewer": "Jules"},
    }
    report = ValidationReport(**data)
    assert report.source == "manual-audit"
    assert report.commit_identifier == "perf-8888"
    assert report.validation_results["security_clear"] is True
    assert report.evidence_references == ["audit-doc-v1"]
    assert report.confidence_metadata["human_reviewer"] == "Jules"


def test_validation_report_invalid_payload():
    """Test ValidationReport validation failures on malformed data."""
    # Missing source
    bad_data = {
        "timestamp": "2026-03-31T12:00:00Z",
        "commit_identifier": "feat-1234",
        "validation_results": {},
        "evidence_references": [],
        "confidence_metadata": {},
    }
    with pytest.raises(ValidationError):
        ValidationReport(**bad_data)


def test_deployment_event_schema_snake_case():
    """Test DeploymentEvent parses correct snake_case payload."""
    data = {
        "source": "github-actions",
        "deployment_target": "production-cluster",
        "status": "success",
        "commit_identifier": "deploy-5678",
        "log_payload": {"duration_seconds": 120, "errors": []},
    }
    event = DeploymentEvent(**data)
    assert event.source == "github-actions"
    assert event.deployment_target == "production-cluster"
    assert event.status == "success"
    assert event.commit_identifier == "deploy-5678"
    assert event.log_payload["duration_seconds"] == 120


def test_deployment_event_schema_spaced_keys():
    """Test DeploymentEvent parses correct spaced-key payload."""
    data = {
        "source": "gitlab-ci",
        "deployment target": "staging-environment",
        "status": "failed",
        "commit identifier": "rollback-1111",
        "log payload": {"reason": "health check timeout"},
    }
    event = DeploymentEvent(**data)
    assert event.source == "gitlab-ci"
    assert event.deployment_target == "staging-environment"
    assert event.status == "failed"
    assert event.commit_identifier == "rollback-1111"
    assert event.log_payload["reason"] == "health check timeout"


def test_deployment_event_invalid():
    """Test DeploymentEvent validation failures on malformed data."""
    bad_data = {
        "source": "github-actions",
        "deployment_target": "production-cluster",
        "status": "success",
        # Missing commit identifier and log payload
    }
    with pytest.raises(ValidationError):
        DeploymentEvent(**bad_data)


def test_architecture_decision_schema_snake_case():
    """Test ArchitectureDecision parses correct snake_case payload."""
    data = {
        "proposal": "ADR-005-use-postgres",
        "reasoning": "Postgres is highly robust and matches relational needs.",
        "validation_requirements": ["compliance-audit", "stress-test-1000-qps"],
        "approval_state": "accepted",
    }
    decision = ArchitectureDecision(**data)
    assert decision.proposal == "ADR-005-use-postgres"
    assert decision.reasoning == "Postgres is highly robust and matches relational needs."
    assert decision.validation_requirements == ["compliance-audit", "stress-test-1000-qps"]
    assert decision.approval_state == "accepted"


def test_architecture_decision_schema_spaced_keys():
    """Test ArchitectureDecision parses correct spaced-key payload."""
    data = {
        "proposal": "ADR-006-migration",
        "reasoning": "Decouple services",
        "validation requirements": ["e2e-suite"],
        "approval state": "pending-review",
    }
    decision = ArchitectureDecision(**data)
    assert decision.proposal == "ADR-006-migration"
    assert decision.reasoning == "Decouple services"
    assert decision.validation_requirements == ["e2e-suite"]
    assert decision.approval_state == "pending-review"


def test_architecture_decision_invalid():
    """Test ArchitectureDecision validation failures on malformed data."""
    bad_data = {
        "proposal": "ADR-007",
        # Missing reasoning and approval state
    }
    with pytest.raises(ValidationError):
        ArchitectureDecision(**bad_data)


def test_process_incoming_payload_valid_report(temp_runtime):
    """Test process_incoming_payload handles valid validation reports, preserves lineage and does not write to archive."""
    payload_data = {
        "source": "github-actions-ci",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "98a7c6f",
        "validation_results": {"is_passing": True, "failed_tests": []},
        "evidence_references": ["run-id-12345"],
        "confidence_metadata": {"reliability_score": 1.0},
    }

    initial_memory_count = len(temp_runtime.memory.list_all())
    initial_archive_count = len(temp_runtime.archive.list_all())

    # Process ingestion via deterministic intake gateway
    result = process_incoming_payload("validation_report", payload_data, temp_runtime)

    # Verify result
    assert result["status"] == "success"
    assert "memory_id" in result
    assert result["payload_type"] == "validation_report"

    # Verify memory store contains the newly created hypothesis memory object
    memories = temp_runtime.memory.list_all()
    assert len(memories) == initial_memory_count + 1

    stored_obj = temp_runtime.memory.retrieve(result["memory_id"])
    assert stored_obj is not None
    assert stored_obj.object_type == "skal_validation_report"
    assert stored_obj.confidence == ConfidenceLevel.HYPOTHESIS
    assert stored_obj.content["source"] == "github-actions-ci"
    assert stored_obj.content["commit_identifier"] == "98a7c6f"

    # Metadata preservation & tags verification
    assert "skal" in stored_obj.tags
    assert "validation_report" in stored_obj.tags
    assert "github-actions-ci" in stored_obj.tags
    assert "98a7c6f" in stored_obj.tags

    # Evidence tracking & Lineage preservation verification
    # Ensure permanent archive has NOT been modified
    assert len(temp_runtime.archive.list_all()) == initial_archive_count


def test_process_incoming_payload_invalid_type(temp_runtime):
    """Test process_incoming_payload rejects unsupported payload types."""
    with pytest.raises(ValueError, match="Unsupported SAGE-SKAL payload type"):
        process_incoming_payload("unknown_type", {}, temp_runtime)


def test_process_incoming_payload_malformed_data(temp_runtime):
    """Test process_incoming_payload rejects malformed data with ValueError."""
    bad_payload = {
        "source": "faulty-src",
        # missing mandatory fields
    }
    with pytest.raises(ValueError, match="SAGE-SKAL schema validation failed"):
        process_incoming_payload("validation_report", bad_payload, temp_runtime)


def test_skal_api_intake_integration():
    """Test API integration for the /tools/skal/intake endpoint."""
    from sage.api import app, runtime, validation

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override the global API runtime
        runtime.__init__(workspace_path=tmpdir)
        runtime.start()
        validation.__init__(runtime.memory, runtime.archive)

        with TestClient(app) as client:
            # 1. Test valid deployment event (spaced keys)
            payload = {
                "payload_type": "deployment_event",
                "payload_data": {
                    "source": "argocd",
                    "deployment target": "kubernetes-prod",
                    "status": "active-live",
                    "commit identifier": "sha-abcde123",
                    "log payload": {"replications": 3, "healthy": True},
                },
            }
            response = client.post("/tools/skal/intake", json=payload)
            assert response.status_code == 200
            res_data = response.json()
            assert res_data["status"] == "success"
            assert res_data["payload_type"] == "deployment_event"
            assert "memory_id" in res_data
            assert res_data["data"]["deployment_target"] == "kubernetes-prod"

            # 2. Test invalid / malformed payload (missing approval state)
            bad_payload = {
                "payload_type": "architecture_decision",
                "payload_data": {
                    "proposal": "ADR-009-graphql",
                    "reasoning": "Decouple API queries",
                    "validation_requirements": ["perf-benchmarks"],
                    # missing approval_state
                },
            }
            response = client.post("/tools/skal/intake", json=bad_payload)
            assert response.status_code == 400
            assert "SAGE-SKAL schema validation failed" in response.json()["detail"]

            # 3. Test invalid payload type
            bad_type_payload = {
                "payload_type": "wrong_type_here",
                "payload_data": {"some": "data"},
            }
            response = client.post("/tools/skal/intake", json=bad_type_payload)
            assert response.status_code == 400
            assert "Unsupported SAGE-SKAL payload type" in response.json()["detail"]


def test_promote_validation_report_approved(temp_runtime):
    """Test that an approved validation report is successfully promoted to the Master Archive."""
    payload_data = {
        "source": "github-actions-ci",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "98a7c6f",
        "validation_results": {"is_passing": True, "failed_tests": []},
        "evidence_references": ["run-id-12345"],
        "confidence_metadata": {"reliability_score": 1.0},
    }

    # Intake
    intake_res = process_incoming_payload("validation_report", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Promote with approval
    promote_res = promote_skal_payload(
        memory_id=memory_id, approved=True, approver="Jules", runtime=temp_runtime
    )

    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Master Archive"
    assert "archive_id" in promote_res

    # Verify storage contains promoted archive entry
    archive_entry = temp_runtime.archive.retrieve_entry(promote_res["archive_id"])
    assert archive_entry is not None
    assert archive_entry.title.startswith("Validated Report:")
    assert archive_entry.intelligence.confidence.confidence_level == 1.0

    # Verify memory object was marked archived
    stored_mem = temp_runtime.memory.retrieve(memory_id)
    assert stored_mem.confidence == ConfidenceLevel.ARCHIVED


def test_promote_validation_report_unapproved(temp_runtime):
    """Test that an unapproved validation report is routed to the Validation Lab instead of Master Archive."""
    payload_data = {
        "source": "manual-ci",
        "timestamp": "2026-03-31T20:15:00Z",
        "commit_identifier": "98a7c6f",
        "validation_results": {"is_passing": False, "failed_tests": ["test_api"]},
        "evidence_references": ["run-id-12345"],
        "confidence_metadata": {"reliability_score": 0.5},
    }

    # Intake
    intake_res = process_incoming_payload("validation_report", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Promote with approved=False
    promote_res = promote_skal_payload(
        memory_id=memory_id, approved=False, approver="Jules", runtime=temp_runtime
    )

    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Validation Lab"

    # Verify it is NOT in Master Archive
    archive_entries = temp_runtime.archive.list_all()
    assert len(archive_entries) == 0


def test_promote_architecture_decision_approved(temp_runtime):
    """Test that an approved architecture decision is successfully promoted and records technical decision lineage."""
    payload_data = {
        "proposal": "ADR-010-redis-cache",
        "reasoning": "Using Redis will decrease latency of session rehydration",
        "validation_requirements": ["load-test-500-rps"],
        "approval_state": "accepted",
    }

    # Intake
    intake_res = process_incoming_payload("architecture_decision", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Promote with approval
    promote_res = promote_skal_payload(
        memory_id=memory_id, approved=True, approver="Jules", runtime=temp_runtime
    )

    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Master Archive"
    assert "archive_id" in promote_res
    assert "decision_id" in promote_res

    # Verify recorded decision lineage inside archive entry
    archive_entry = temp_runtime.archive.retrieve_entry(promote_res["archive_id"])
    assert archive_entry is not None
    assert promote_res["decision_id"] in archive_entry.decision_history

    # Verify decision tracker contains the decision
    decision = temp_runtime.decisions.retrieve_decision(promote_res["decision_id"])
    assert decision is not None
    assert decision.description == "ADR-010-redis-cache"


def test_promote_architecture_decision_unapproved(temp_runtime):
    """Test that an unapproved architecture decision is routed to the Engineering Lab."""
    payload_data = {
        "proposal": "ADR-011-experimental",
        "reasoning": "Experimental reasoning",
        "validation_requirements": ["poc-tests"],
        "approval_state": "pending",
    }

    # Intake
    intake_res = process_incoming_payload("architecture_decision", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Promote with approved=False
    promote_res = promote_skal_payload(
        memory_id=memory_id, approved=False, approver="Jules", runtime=temp_runtime
    )

    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Engineering Lab"


def test_promote_deployment_event(temp_runtime):
    """Test that a deployment event updates the operational state only and goes to the Command Center."""
    payload_data = {
        "source": "argocd",
        "deployment_target": "production-onrender",
        "status": "synchronized",
        "commit_identifier": "deploy-render-123",
        "log_payload": {"healthy": True},
    }

    # Intake
    intake_res = process_incoming_payload("deployment_event", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Promote
    promote_res = promote_skal_payload(
        memory_id=memory_id, approved=True, approver="Jules", runtime=temp_runtime
    )

    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Command Center"

    # Verify operational state updated
    assert (
        temp_runtime.current_state.active_task
        == "Deploy Target: production-onrender [synchronized]"
    )

    # Verify it did not enter the Master Archive
    assert len(temp_runtime.archive.list_all()) == 0


def test_promote_research_restrictions(temp_runtime):
    """Test that research items are restricted from entering the Master Archive directly."""
    payload_data = {
        "proposal": "SAGE-RF-FutureExpansion",
        "reasoning": "Highly experimental mathematical reasoning",
        "validation_requirements": ["theoretical-proofs"],
        "approval_state": "draft",
    }

    # Intake
    intake_res = process_incoming_payload("architecture_decision", payload_data, temp_runtime)
    memory_id = intake_res["memory_id"]

    # Attempt to bypass restriction by promoting a research item with approved=True
    with pytest.raises(ValueError, match="Research items cannot directly enter Master Archive"):
        promote_skal_payload(
            memory_id=memory_id,
            approved=True,
            approver="Jules",
            runtime=temp_runtime,
            is_research=True,
        )

    # Standard unapproved routing should route successfully to the Research Lab
    promote_res = promote_skal_payload(
        memory_id=memory_id,
        approved=False,
        approver="Jules",
        runtime=temp_runtime,
        is_research=True,
    )
    assert promote_res["status"] == "success"
    assert promote_res["destination"] == "Research Lab"


def test_skal_api_promote_integration():
    """Test SAGE-SKAL knowledge promotion contract integration via API."""
    from sage.api import app, runtime, validation

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override global runtime
        runtime.__init__(workspace_path=tmpdir)
        runtime.start()
        validation.__init__(runtime.memory, runtime.archive)

        with TestClient(app) as client:
            # 1. Ingest a validation report
            intake_payload = {
                "payload_type": "validation_report",
                "payload_data": {
                    "source": "api-tests",
                    "timestamp": "2026-03-31T22:00:00Z",
                    "commit identifier": "sha-api-99",
                    "validation results": {"passed": True},
                    "evidence references": ["ref-1"],
                    "confidence metadata": {"score": 1.0},
                },
            }
            intake_response = client.post("/tools/skal/intake", json=intake_payload)
            assert intake_response.status_code == 200
            memory_id = intake_response.json()["memory_id"]

            # 2. Promote with valid approved=True signature
            promote_payload = {
                "memory_id": memory_id,
                "approved": True,
                "approver": "Jules",
                "is_research": False,
            }
            promote_response = client.post("/tools/skal/promote", json=promote_payload)
            assert promote_response.status_code == 200
            assert promote_response.json()["destination"] == "Master Archive"
            assert "archive_id" in promote_response.json()

            # 3. Ingest another item to test research bypass rejection
            intake_payload2 = {
                "payload_type": "architecture_decision",
                "payload_data": {
                    "proposal": "ADR-Experimental-Quantum",
                    "reasoning": "Quantum databases",
                    "validation requirements": ["paper-review"],
                    "approval state": "speculative",
                },
            }
            intake_response2 = client.post("/tools/skal/intake", json=intake_payload2)
            assert intake_response2.status_code == 200
            memory_id2 = intake_response2.json()["memory_id"]

            # Try to promote speculative research item with approved=True to Master Archive
            promote_payload2 = {
                "memory_id": memory_id2,
                "approved": True,
                "approver": "Jules",
                "is_research": True,
            }
            promote_response2 = client.post("/tools/skal/promote", json=promote_payload2)
            assert promote_response2.status_code == 400
            assert (
                "Research items cannot directly enter Master Archive"
                in promote_response2.json()["detail"]
            )
